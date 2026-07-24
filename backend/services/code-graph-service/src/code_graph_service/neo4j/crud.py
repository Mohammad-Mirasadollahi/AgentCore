"""Neo4j Store CRUD: symbols, edges, idempotency, outbox, wipe."""

from __future__ import annotations

import json
from typing import Any

from ..core import (
    CallConfidence,
    ConflictError,
    DocStatus,
    GraphEdge,
    GraphSymbol,
    NotFoundError,
    Scope,
    SymbolKind,
)
from . import cypher


class Neo4jCrudMixin:
    """Persistence port methods for CodeSymbol / CODE_REL."""

    @staticmethod
    def _scope_key(scope: Scope) -> str:
        return "|".join((scope.tenant_id, scope.workspace_id, scope.project_id, scope.project_group_id or ""))

    def _symbol_from_node(self, node: Any, scope: Scope) -> GraphSymbol:
        embedding = node.get("embedding") or []
        if isinstance(embedding, str):
            embedding = json.loads(embedding)
        return GraphSymbol(
            id=node["id"],
            scope=scope,
            kind=SymbolKind(node["kind"]),
            file_path=node["file_path"],
            name=node["name"],
            qualified_name=node["qualified_name"],
            signature=node["signature"],
            body=node["body"],
            hash_value=node["hash_value"],
            ai_documentation=node["ai_documentation"],
            doc_status=DocStatus(node["doc_status"]),
            embedding=list(embedding),
            visibility=node["visibility"],
            version=int(node["version"]),
            created_at=str(node["created_at"]),
            updated_at=str(node["updated_at"]),
            language=str(node.get("language") or ""),
        )

    def get_symbol(self, symbol_id: str, scope: Scope) -> GraphSymbol:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                cypher.GET_SYMBOL,
                id=symbol_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
            ).single()
        if record is None:
            raise NotFoundError("symbol not found in project scope")
        return self._symbol_from_node(record["n"], scope)

    def put_symbol(self, symbol: GraphSymbol) -> None:
        scope = symbol.scope
        with self._driver.session(database=self._database) as session:
            session.run(
                cypher.PUT_SYMBOL,
                id=symbol.id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
                project_group_id=scope.project_group_id,
                kind=symbol.kind.value,
                file_path=symbol.file_path,
                name=symbol.name,
                qualified_name=symbol.qualified_name,
                signature=symbol.signature,
                body=symbol.body,
                hash_value=symbol.hash_value,
                ai_documentation=symbol.ai_documentation,
                doc_status=symbol.doc_status.value,
                embedding=list(symbol.embedding),
                visibility=symbol.visibility,
                version=symbol.version,
                created_at=symbol.created_at,
                updated_at=symbol.updated_at,
                language=symbol.language or "",
            )

    def delete_symbol(self, symbol_id: str, scope: Scope) -> None:
        with self._driver.session(database=self._database) as session:
            session.run(
                cypher.DELETE_SYMBOL,
                id=symbol_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
            )

    def list_symbols(self, scope: Scope) -> list[GraphSymbol]:
        with self._driver.session(database=self._database) as session:
            rows = list(
                session.run(
                    cypher.LIST_SYMBOLS,
                    tenant_id=scope.tenant_id,
                    workspace_id=scope.workspace_id,
                    project_id=scope.project_id,
                )
            )
        return [self._symbol_from_node(row["n"], scope) for row in rows]

    def list_symbols_for_file(self, scope: Scope, file_path: str) -> list[GraphSymbol]:
        path = str(file_path or "").replace("\\", "/")
        with self._driver.session(database=self._database) as session:
            rows = list(
                session.run(
                    cypher.LIST_SYMBOLS_FOR_FILE,
                    tenant_id=scope.tenant_id,
                    workspace_id=scope.workspace_id,
                    project_id=scope.project_id,
                    file_path=path,
                )
            )
        return [self._symbol_from_node(row["n"], scope) for row in rows]

    def get_symbol_by_qualified_name(self, scope: Scope, qualified_name: str) -> GraphSymbol | None:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                cypher.GET_SYMBOL_BY_QUALIFIED_NAME,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
                qualified_name=qualified_name,
            ).single()
        if record is None:
            return None
        return self._symbol_from_node(record["n"], scope)

    def delete_file_edges(self, scope: Scope, file_path: str) -> None:
        with self._driver.session(database=self._database) as session:
            session.run(
                cypher.DELETE_FILE_EDGES,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
                file_path=file_path,
            )

    def delete_edge(self, scope: Scope, edge_id: str) -> None:
        with self._driver.session(database=self._database) as session:
            session.run(
                cypher.DELETE_EDGE,
                id=edge_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
            )

    def put_edge(self, edge: GraphEdge) -> None:
        scope = edge.scope
        metadata = dict(edge.metadata or {})
        file_path = str(metadata.get("file_path") or "")
        with self._driver.session(database=self._database) as session:
            session.run(
                cypher.PUT_EDGE,
                id=edge.id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
                project_group_id=scope.project_group_id,
                rel_type=edge.rel_type,
                confidence=edge.confidence.value,
                file_path=file_path,
                metadata_json=json.dumps(metadata, sort_keys=True),
            )

    def list_edges(self, scope: Scope) -> list[GraphEdge]:
        with self._driver.session(database=self._database) as session:
            rows = list(
                session.run(
                    cypher.LIST_EDGES,
                    tenant_id=scope.tenant_id,
                    workspace_id=scope.workspace_id,
                    project_id=scope.project_id,
                )
            )
        return [
            GraphEdge(
                id=row["id"],
                scope=scope,
                rel_type=row["rel_type"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                confidence=CallConfidence(row["confidence"]),
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
            for row in rows
        ]

    def begin_idempotency(self, scope: Scope, key: str, resource: str) -> str | None:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                cypher.BEGIN_IDEMPOTENCY,
                scope_key=self._scope_key(scope),
                idempotency_key=key,
                resource_type=resource,
            ).single()
        return None if record is None else record["resource_id"]

    def complete_idempotency(self, scope: Scope, key: str, resource: str, resource_id: str) -> None:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                cypher.COMPLETE_IDEMPOTENCY,
                scope_key=self._scope_key(scope),
                idempotency_key=key,
                resource_type=resource,
                resource_id=resource_id,
            ).single()
        if record is None or record["resource_id"] != resource_id:
            raise ConflictError("idempotency key already bound to another resource")

    def append_event(self, event: dict[str, Any]) -> None:
        with self._driver.session(database=self._database) as session:
            session.run(
                cypher.APPEND_EVENT,
                event_id=event["event_id"],
                event_type=event["event_type"],
                payload_json=json.dumps(event, sort_keys=True),
            )

    def outbox(self) -> list[dict[str, Any]]:
        with self._driver.session(database=self._database) as session:
            rows = list(session.run(cypher.OUTBOX))
        return [json.loads(row["payload_json"]) for row in rows]

    def wipe_scope(self, scope: Scope) -> dict[str, int]:
        with self._driver.session(database=self._database) as session:
            symbols = session.run(
                cypher.WIPE_SYMBOLS,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
            ).single()
            edges = session.run(
                cypher.WIPE_EDGES,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
            ).single()
            idem = session.run(
                cypher.WIPE_IDEMPOTENCY,
                scope_key=self._scope_key(scope),
            ).single()
        self._capabilities_cache = None
        return {
            "symbols": int((symbols or {}).get("deleted") or 0),
            "edges": int((edges or {}).get("deleted") or 0),
            "idempotency": int((idem or {}).get("deleted") or 0),
        }
