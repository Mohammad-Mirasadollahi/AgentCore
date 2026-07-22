"""Upsert human-authored documentation nodes into the code graph."""

from __future__ import annotations

from typing import Any

from ...domain.enums import DocStatus, RelType, SymbolKind
from ...domain.errors import ValidationError
from ...domain.hashing import digest, now_iso
from ...domain.models import GraphSymbol, Scope
from ...domain.symbol_resolve import resolve_linked_symbol


def human_doc_symbol_id(project_id: str, doc_id: str) -> str:
    return f"doc:human:{project_id}:{doc_id}"


class HumanDocIngestMixin:
    """Project human Markdown docs as DOCUMENTATION nodes with DOCUMENTED_BY edges."""

    def upsert_human_documentation(
        self,
        scope: Scope,
        *,
        doc_id: str,
        relative_path: str,
        body: str,
        title: str = "",
        linked_symbol_tokens: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Upsert ``doc:human:{project}:{doc_id}`` and edge resolved code symbols.

        Only tokens that resolve to existing code symbols create ``DOCUMENTED_BY``
        edges (code → human doc). Unresolved tokens are reported, never invented.
        """
        doc_id = str(doc_id or "").strip()
        relative_path = str(relative_path or "").strip().replace("\\", "/")
        body = body if isinstance(body, str) else str(body or "")
        if not doc_id or not relative_path:
            raise ValidationError("doc_id and relative_path are required")

        stamp = now_iso()
        symbol_id = human_doc_symbol_id(scope.project_id, doc_id)
        previous = self._maybe_get(symbol_id, scope)
        embed = self.embeddings.embed(f"{title or doc_id}\n{body[:2000]}")
        doc_symbol = GraphSymbol(
            id=symbol_id,
            scope=scope,
            kind=SymbolKind.DOCUMENTATION,
            file_path=relative_path,
            name=f"{title or doc_id}.md" if not relative_path.endswith(".md") else relative_path.rsplit("/", 1)[-1],
            qualified_name=f"human:{doc_id}",
            signature=title or doc_id,
            body=body,
            hash_value=digest(body),
            ai_documentation=body[:4000],
            doc_status=DocStatus.HUMAN,
            embedding=embed.vector,
            version=(previous.version + 1) if previous else 1,
            created_at=previous.created_at if previous else stamp,
            updated_at=stamp,
            language="",
        )
        self.store.put_symbol(doc_symbol)
        self._index_embedding(scope, symbol_id, embed.vector, kind=SymbolKind.DOCUMENTATION.value)

        linked: list[str] = []
        unresolved: list[str] = []
        edges = 0
        for token in linked_symbol_tokens or []:
            text = str(token or "").strip()
            if not text:
                continue
            target = resolve_linked_symbol(self.store, scope, text)
            if target is None:
                unresolved.append(text)
                continue
            edges += self._put_edge(
                scope,
                RelType.DOCUMENTED_BY.value,
                target.id,
                symbol_id,
                file_path=relative_path,
                metadata={"doc_id": doc_id, "origin": "human", **(metadata or {})},
                link_key=f"human:{doc_id}:{target.id}",
            )
            linked.append(target.id)

        linked_set = set(linked)
        removed = 0
        for edge in self.store.list_edges(scope):
            if edge.rel_type != RelType.DOCUMENTED_BY.value:
                continue
            if edge.target_id != symbol_id:
                continue
            if edge.metadata.get("origin") != "human":
                continue
            if edge.metadata.get("doc_id") != doc_id:
                continue
            if edge.source_id in linked_set:
                continue
            self.store.delete_edge(scope, edge.id)
            removed += 1

        return {
            "doc_symbol_id": symbol_id,
            "doc_id": doc_id,
            "relative_path": relative_path,
            "linked_symbol_ids": linked,
            "unresolved_tokens": unresolved,
            "edges_written": edges,
            "edges_removed": removed,
        }
