"""Query use cases: symbol lookup, structural/semantic search, polyglot profile."""

from __future__ import annotations

from typing import Any

from ..domain.embeddings import cosine
from ..domain.enums import SymbolKind
from ..domain.errors import NotFoundError, ValidationError
from ..domain.models import GraphSymbol, Scope
from ..domain.polyglot_profile import PolyglotProjectProfile, build_polyglot_profile
from ..domain.rag import (
    DEFAULT_EXPAND_DEPTH,
    DEFAULT_EXPAND_EDGE_LIMIT,
    DEFAULT_EXPAND_SEEDS,
    SEARCHABLE_SYMBOL_KINDS,
)
from .support import GraphServiceSupport


class QueryUseCases(GraphServiceSupport):
    def get_symbol(self, scope: Scope, symbol_id: str) -> GraphSymbol:
        return self.store.get_symbol(symbol_id, scope)

    def list_changed_since(self, scope: Scope, previous_hashes: dict[str, str]) -> list[GraphSymbol]:
        changed: list[GraphSymbol] = []
        for symbol in self.store.list_symbols(scope):
            if symbol.kind in {SymbolKind.FILE, SymbolKind.DOCUMENTATION, SymbolKind.UNRESOLVED}:
                continue
            prior = previous_hashes.get(symbol.qualified_name)
            if prior is None or prior != symbol.hash_value:
                changed.append(symbol)
        return changed

    def get_polyglot_profile(self, scope: Scope) -> PolyglotProjectProfile:
        return build_polyglot_profile(self.store.list_symbols(scope), self.store.list_edges(scope))

    def structural_query(
        self,
        scope: Scope,
        symbol_id: str,
        rel_type: str | None = None,
        *,
        max_depth: int = 1,
    ) -> dict[str, Any]:
        symbol = self.store.get_symbol(symbol_id, scope)
        expand = getattr(self.store, "expand_neighborhood", None)
        caps = getattr(self.store, "capabilities", None)
        cap_map = caps() if callable(caps) else {}
        if callable(expand) and max_depth > 1:
            edges = expand(scope, symbol_id, max_depth=max_depth, rel_type=rel_type)
            expansion = "apoc_expand" if cap_map.get("apoc") else "store_expand"
        else:
            edges = [
                edge
                for edge in self.store.list_edges(scope)
                if edge.source_id == symbol_id or edge.target_id == symbol_id
            ]
            if rel_type:
                edges = [edge for edge in edges if edge.rel_type == rel_type.upper()]
            expansion = "one_hop"
        payload = {
            "symbol": self._symbol_view(symbol),
            "max_depth": max_depth,
            "expansion": expansion,
            "edges": [
                {
                    "id": edge.id,
                    "rel_type": edge.rel_type,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "confidence": edge.confidence.value,
                    "metadata": edge.metadata,
                }
                for edge in edges
            ],
        }
        rank = getattr(self.store, "rank_symbols_by_degree", None)
        if cap_map:
            payload["neo4j_capabilities"] = cap_map
        if callable(rank) and max_depth > 1:
            payload["importance_hints"] = rank(scope, top_k=8)
        return payload

    def semantic_search(
        self,
        scope: Scope,
        query: str,
        top_k: int = 5,
        *,
        expand_seeds: int = DEFAULT_EXPAND_SEEDS,
        expand_depth: int = DEFAULT_EXPAND_DEPTH,
    ) -> list[dict[str, Any]]:
        """Stage-1 hybrid RAG: kind-filtered pgvector (or in-store) → Neo4j expand on top seeds.

        turbovec is not used here (Stage-2 optional accelerator only).
        """
        if not query.strip():
            raise ValidationError("query is required")
        vector = self.embeddings.embed(query, is_query=True).vector
        top_k = max(1, top_k)
        expand_seeds = max(0, min(int(expand_seeds), top_k))
        expand_depth = max(1, min(int(expand_depth), 3))

        hits: list[dict[str, Any]] = []
        retrieval = "in_store_cosine"
        if self.embedding_index is not None:
            retrieval = "pgvector"
            # Over-fetch slightly so orphan cleanup / missing store rows do not starve top_k.
            for symbol_id, score in self.embedding_index.search(
                scope,
                vector,
                top_k=max(top_k * 2, top_k),
                kinds=sorted(SEARCHABLE_SYMBOL_KINDS),
            ):
                try:
                    symbol = self.store.get_symbol(symbol_id, scope)
                except NotFoundError:
                    self._delete_embedding(scope, symbol_id)
                    continue
                if symbol.kind.value not in SEARCHABLE_SYMBOL_KINDS:
                    self._delete_embedding(scope, symbol_id)
                    continue
                hits.append(
                    {
                        "score": round(score, 6),
                        "symbol": self._symbol_view(symbol),
                        "retrieval": retrieval,
                    }
                )
                if len(hits) >= top_k:
                    break
        else:
            scored: list[tuple[float, GraphSymbol]] = []
            for symbol in self.store.list_symbols(scope):
                if symbol.kind.value not in SEARCHABLE_SYMBOL_KINDS:
                    continue
                scored.append((cosine(vector, symbol.embedding), symbol))
            scored.sort(key=lambda item: (-item[0], item[1].qualified_name))
            for score, symbol in scored[:top_k]:
                if score <= 0:
                    continue
                hits.append(
                    {
                        "score": round(score, 6),
                        "symbol": self._symbol_view(symbol),
                        "retrieval": retrieval,
                    }
                )

        self._attach_graph_neighbors(
            scope,
            hits,
            expand_seeds=expand_seeds,
            expand_depth=expand_depth,
        )
        return hits[:top_k]

    def _attach_graph_neighbors(
        self,
        scope: Scope,
        hits: list[dict[str, Any]],
        *,
        expand_seeds: int,
        expand_depth: int,
    ) -> None:
        if not hits or expand_seeds <= 0:
            return
        expand = getattr(self.store, "expand_neighborhood", None)
        for hit in hits[:expand_seeds]:
            seed_id = str(hit["symbol"]["id"])
            if callable(expand):
                try:
                    graph_edges = expand(
                        scope,
                        seed_id,
                        max_depth=expand_depth,
                        limit=DEFAULT_EXPAND_EDGE_LIMIT,
                    )
                    expansion = "apoc_or_store_expand" if expand_depth > 1 else "store_expand"
                except Exception:
                    graph_edges = [
                        edge
                        for edge in self.store.list_edges(scope)
                        if edge.source_id == seed_id or edge.target_id == seed_id
                    ][:DEFAULT_EXPAND_EDGE_LIMIT]
                    expansion = "one_hop_fallback"
            else:
                graph_edges = [
                    edge
                    for edge in self.store.list_edges(scope)
                    if edge.source_id == seed_id or edge.target_id == seed_id
                ][:DEFAULT_EXPAND_EDGE_LIMIT]
                expansion = "one_hop"
            hit["graph_neighbors"] = [
                {
                    "id": edge.id,
                    "rel_type": edge.rel_type,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                }
                for edge in graph_edges
            ]
            hit["graph_expansion"] = expansion
            # Light hybrid boost: structural connectivity hints denser local context.
            neighbor_count = len(hit["graph_neighbors"])
            if neighbor_count:
                hit["score"] = round(min(1.0, float(hit["score"]) + 0.01 * min(neighbor_count, 5)), 6)
