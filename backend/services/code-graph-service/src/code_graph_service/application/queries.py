"""Query use cases: symbol lookup, structural/semantic search, polyglot profile."""

from __future__ import annotations

from typing import Any

from ..domain.embeddings import cosine
from ..domain.errors import NotFoundError, ValidationError
from ..domain.impact import directed_impact, escalate_hint, rank_callers
from ..domain.models import GraphSymbol, Scope
from ..domain.polyglot_profile import PolyglotProjectProfile, build_polyglot_profile
from ..domain.rag import (
    DEFAULT_EXPAND_DEPTH,
    DEFAULT_EXPAND_EDGE_LIMIT,
    DEFAULT_EXPAND_SEEDS,
    SEARCHABLE_SYMBOL_KINDS,
)
from ..domain.unused_candidates import find_unused_candidates
from .support import GraphServiceSupport


class QueryUseCases(GraphServiceSupport):
    def get_symbol(self, scope: Scope, symbol_id: str) -> GraphSymbol:
        return self.store.get_symbol(symbol_id, scope)

    def unused_candidates(
        self,
        scope: Scope,
        *,
        scope_mode: str,
        anchor_symbols: list[str] | None = None,
        anchor_paths: list[str] | None = None,
        max_results: int = 50,
        include_uncertain: bool = False,
    ) -> dict[str, Any]:
        banner = (
            self.freshness_status(scope)
            if hasattr(self, "freshness_status")
            else {"pending_files": [], "is_stale": False}
        )
        pending = banner.get("pending_files") or banner.get("pending") or []
        if pending:
            freshness = "pending_sync"
        elif banner.get("is_stale") or banner.get("stale"):
            freshness = "stale"
        else:
            freshness = "ok"
        try:
            payload = find_unused_candidates(
                self.store.list_symbols(scope),
                self.store.list_edges(scope),
                scope_mode=scope_mode,
                anchor_symbols=anchor_symbols,
                anchor_paths=anchor_paths,
                max_results=max_results,
                include_uncertain=include_uncertain,
                freshness=freshness,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        payload["freshness_detail"] = {
            "pending_files": pending if isinstance(pending, list) else [],
            "last_sync_at": banner.get("last_sync_at"),
        }
        return payload

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
            "reference_kind": "structural",
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
        payload["escalate_hint"] = escalate_hint(sparse=len(payload["edges"]) == 0)
        freshness_fn = getattr(self, "freshness_status", None)
        if callable(freshness_fn):
            payload["freshness"] = freshness_fn(scope)
        return payload

    def callers(
        self,
        scope: Scope,
        symbol_id: str,
        *,
        top_k: int = 20,
        max_depth: int = 1,
        min_confidence: str | None = None,
        rel_types: list[str] | None = None,
    ) -> dict[str, Any]:
        symbol = self.store.get_symbol(symbol_id, scope)
        symbols = {s.id: s for s in self.store.list_symbols(scope)}
        allowed = frozenset(r.upper() for r in rel_types) if rel_types else None
        edges = self._structural_edges_for_seed(
            scope,
            symbol.id,
            max_depth=max_depth,
            direction="upstream",
            rel_types=list(allowed) if allowed else None,
        )
        payload = rank_callers(
            symbol.id,
            symbols,
            edges,
            top_k=top_k,
            max_depth=max_depth,
            min_confidence=min_confidence,
            rel_types=allowed,
        )
        payload["symbol"] = self._symbol_view(symbol)
        freshness_fn = getattr(self, "freshness_status", None)
        if callable(freshness_fn):
            payload["freshness"] = freshness_fn(scope)
        return payload

    def impact_analysis(
        self,
        scope: Scope,
        symbol_id: str,
        *,
        direction: str = "both",
        max_depth: int = 3,
        min_confidence: str | None = None,
        rel_types: list[str] | None = None,
        top_k: int = 50,
        include_legacy_expand: bool = True,
    ) -> dict[str, Any]:
        symbol = self.store.get_symbol(symbol_id, scope)
        symbols = {s.id: s for s in self.store.list_symbols(scope)}
        allowed = frozenset(r.upper() for r in rel_types) if rel_types else None
        edges = self._structural_edges_for_seed(
            scope,
            symbol.id,
            max_depth=max_depth,
            direction=direction,
            rel_types=list(allowed) if allowed else None,
        )
        payload = directed_impact(
            symbol.id,
            symbols,
            edges,
            direction=direction,
            max_depth=max_depth,
            min_confidence=min_confidence,
            rel_types=allowed,
            top_k=top_k,
        )
        payload["symbol"] = self._symbol_view(symbol)
        if include_legacy_expand:
            legacy = self.structural_query(
                scope,
                symbol.id,
                None if not rel_types else rel_types[0],
                max_depth=max_depth,
            )
            payload["edges"] = legacy.get("edges") or []
            payload["expansion"] = legacy.get("expansion")
            if "importance_hints" in legacy:
                payload["importance_hints"] = legacy["importance_hints"]
            if "neo4j_capabilities" in legacy:
                payload["neo4j_capabilities"] = legacy["neo4j_capabilities"]
        freshness_fn = getattr(self, "freshness_status", None)
        if callable(freshness_fn):
            payload["freshness"] = freshness_fn(scope)
        return payload

    def _structural_edges_for_seed(
        self,
        scope: Scope,
        seed_id: str,
        *,
        max_depth: int,
        direction: str,
        rel_types: list[str] | None,
    ) -> list[Any]:
        """Prefer Neo4j Cypher neighborhood when available; else full in-memory edge list."""
        fetch = getattr(self.store, "neighborhood_edges", None)
        if callable(fetch):
            try:
                edges = fetch(
                    scope,
                    seed_id,
                    max_depth=max_depth,
                    direction=direction,
                    rel_types=rel_types,
                )
                if edges:
                    return list(edges)
            except Exception:
                pass
        return list(self.store.list_edges(scope))

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
