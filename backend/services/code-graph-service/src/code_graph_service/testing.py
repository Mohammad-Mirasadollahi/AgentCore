from __future__ import annotations

from copy import deepcopy
from typing import Any

from .core import ConflictError, GraphEdge, GraphSymbol, NotFoundError, Scope


class InMemoryStore:
    """Deterministic graph Store fake for unit and transport-contract tests."""

    def __init__(self) -> None:
        self._symbols: dict[str, GraphSymbol] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._idempotency: dict[tuple[str, str, str], str] = {}
        self._events: list[dict[str, Any]] = []

    @staticmethod
    def _scope_key(scope: Scope) -> str:
        return "|".join((scope.tenant_id, scope.workspace_id, scope.project_id, scope.project_group_id or ""))

    @staticmethod
    def _same_project(left: Scope, right: Scope) -> bool:
        return (left.tenant_id, left.workspace_id, left.project_id) == (
            right.tenant_id,
            right.workspace_id,
            right.project_id,
        )

    def get_symbol(self, symbol_id: str, scope: Scope) -> GraphSymbol:
        item = self._symbols.get(symbol_id)
        if item is None or not self._same_project(item.scope, scope):
            raise NotFoundError("symbol not found in project scope")
        return deepcopy(item)

    def put_symbol(self, symbol: GraphSymbol) -> None:
        self._symbols[symbol.id] = deepcopy(symbol)

    def list_symbols(self, scope: Scope) -> list[GraphSymbol]:
        items = [item for item in self._symbols.values() if self._same_project(item.scope, scope)]
        return deepcopy(sorted(items, key=lambda item: (item.qualified_name, item.id)))

    def get_symbol_by_qualified_name(self, scope: Scope, qualified_name: str) -> GraphSymbol | None:
        for item in self._symbols.values():
            if self._same_project(item.scope, scope) and item.qualified_name == qualified_name:
                return deepcopy(item)
        return None

    def delete_file_edges(self, scope: Scope, file_path: str) -> None:
        drop = [
            edge_id
            for edge_id, edge in self._edges.items()
            if self._same_project(edge.scope, scope) and edge.metadata.get("file_path") == file_path
        ]
        for edge_id in drop:
            del self._edges[edge_id]

    def put_edge(self, edge: GraphEdge) -> None:
        self._edges[edge.id] = deepcopy(edge)

    def list_edges(self, scope: Scope) -> list[GraphEdge]:
        items = [item for item in self._edges.values() if self._same_project(item.scope, scope)]
        return deepcopy(sorted(items, key=lambda item: item.id))

    def begin_idempotency(self, scope: Scope, key: str, resource: str) -> str | None:
        packed = (self._scope_key(scope), key, resource)
        if packed in self._idempotency:
            return self._idempotency[packed]
        return None

    def complete_idempotency(self, scope: Scope, key: str, resource: str, resource_id: str) -> None:
        packed = (self._scope_key(scope), key, resource)
        if packed in self._idempotency and self._idempotency[packed] != resource_id:
            raise ConflictError("idempotency key already bound to another resource")
        self._idempotency[packed] = resource_id

    def append_event(self, event: dict[str, Any]) -> None:
        self._events.append(deepcopy(event))

    def outbox(self) -> list[dict[str, Any]]:
        return deepcopy(self._events)
