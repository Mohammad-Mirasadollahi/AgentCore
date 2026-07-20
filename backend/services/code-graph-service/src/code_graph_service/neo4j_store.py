from __future__ import annotations

import json
from typing import Any

from .core import (
    CallConfidence,
    ConflictError,
    DocStatus,
    GraphEdge,
    GraphSymbol,
    NotFoundError,
    Scope,
    SymbolKind,
)

# Structural graph edges share one relationship type; `rel_type` carries CALLS/IMPORTS/etc.
_REL = "CODE_REL"


class Neo4jStore:
    """Neo4j adapter for the Code Graph Store port (structural graph + outbox)."""

    def __init__(
        self,
        *,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
        driver: Any | None = None,
        ensure_schema: bool = True,
    ) -> None:
        if driver is None:
            if not uri.startswith(("bolt://", "bolt+s://", "neo4j://", "neo4j+s://")):
                raise ValueError("Neo4j URI must use bolt://, bolt+s://, neo4j://, or neo4j+s://")
            try:
                from neo4j import GraphDatabase
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("neo4j package is required for Neo4j persistence") from exc
            driver = GraphDatabase.driver(uri, auth=(user, password))
        self._driver = driver
        self._database = database
        if ensure_schema:
            self.ensure_schema()

    def close(self) -> None:
        close = getattr(self._driver, "close", None)
        if callable(close):
            close()

    def ensure_schema(self) -> None:
        statements = (
            "CREATE CONSTRAINT code_symbol_id IF NOT EXISTS "
            "FOR (n:CodeSymbol) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT code_outbox_event_id IF NOT EXISTS "
            "FOR (n:CodeOutboxEvent) REQUIRE n.event_id IS UNIQUE",
            "CREATE CONSTRAINT code_idempotency_key IF NOT EXISTS "
            "FOR (n:CodeIdempotency) REQUIRE (n.scope_key, n.idempotency_key, n.resource_type) IS UNIQUE",
            "CREATE INDEX code_symbol_scope IF NOT EXISTS "
            "FOR (n:CodeSymbol) ON (n.tenant_id, n.workspace_id, n.project_id)",
            "CREATE INDEX code_symbol_qualified_name IF NOT EXISTS "
            "FOR (n:CodeSymbol) ON (n.project_id, n.qualified_name)",
        )
        with self._driver.session(database=self._database) as session:
            for statement in statements:
                session.run(statement)

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
        )

    def get_symbol(self, symbol_id: str, scope: Scope) -> GraphSymbol:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                """
                MATCH (n:CodeSymbol {id: $id})
                WHERE n.tenant_id = $tenant_id
                  AND n.workspace_id = $workspace_id
                  AND n.project_id = $project_id
                RETURN n
                """,
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
                """
                MERGE (n:CodeSymbol {id: $id})
                SET n.tenant_id = $tenant_id,
                    n.workspace_id = $workspace_id,
                    n.project_id = $project_id,
                    n.project_group_id = $project_group_id,
                    n.kind = $kind,
                    n.file_path = $file_path,
                    n.name = $name,
                    n.qualified_name = $qualified_name,
                    n.signature = $signature,
                    n.body = $body,
                    n.hash_value = $hash_value,
                    n.ai_documentation = $ai_documentation,
                    n.doc_status = $doc_status,
                    n.embedding = $embedding,
                    n.visibility = $visibility,
                    n.version = $version,
                    n.created_at = $created_at,
                    n.updated_at = $updated_at
                """,
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
            )

    def list_symbols(self, scope: Scope) -> list[GraphSymbol]:
        with self._driver.session(database=self._database) as session:
            rows = list(
                session.run(
                    """
                    MATCH (n:CodeSymbol)
                    WHERE n.tenant_id = $tenant_id
                      AND n.workspace_id = $workspace_id
                      AND n.project_id = $project_id
                    RETURN n
                    ORDER BY n.qualified_name, n.id
                    """,
                    tenant_id=scope.tenant_id,
                    workspace_id=scope.workspace_id,
                    project_id=scope.project_id,
                )
            )
        return [self._symbol_from_node(row["n"], scope) for row in rows]

    def get_symbol_by_qualified_name(self, scope: Scope, qualified_name: str) -> GraphSymbol | None:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                """
                MATCH (n:CodeSymbol)
                WHERE n.tenant_id = $tenant_id
                  AND n.workspace_id = $workspace_id
                  AND n.project_id = $project_id
                  AND n.qualified_name = $qualified_name
                RETURN n
                LIMIT 1
                """,
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
                f"""
                MATCH ()-[r:{_REL}]->()
                WHERE r.tenant_id = $tenant_id
                  AND r.workspace_id = $workspace_id
                  AND r.project_id = $project_id
                  AND r.file_path = $file_path
                DELETE r
                """,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
                file_path=file_path,
            )

    def put_edge(self, edge: GraphEdge) -> None:
        scope = edge.scope
        metadata = dict(edge.metadata or {})
        file_path = str(metadata.get("file_path") or "")
        with self._driver.session(database=self._database) as session:
            session.run(
                f"""
                MATCH (source:CodeSymbol {{id: $source_id}})
                MATCH (target:CodeSymbol {{id: $target_id}})
                MERGE (source)-[r:{_REL} {{id: $id}}]->(target)
                SET r.tenant_id = $tenant_id,
                    r.workspace_id = $workspace_id,
                    r.project_id = $project_id,
                    r.project_group_id = $project_group_id,
                    r.rel_type = $rel_type,
                    r.confidence = $confidence,
                    r.file_path = $file_path,
                    r.metadata_json = $metadata_json
                """,
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
                    f"""
                    MATCH (source:CodeSymbol)-[r:{_REL}]->(target:CodeSymbol)
                    WHERE r.tenant_id = $tenant_id
                      AND r.workspace_id = $workspace_id
                      AND r.project_id = $project_id
                    RETURN r.id AS id,
                           r.rel_type AS rel_type,
                           r.confidence AS confidence,
                           r.metadata_json AS metadata_json,
                           source.id AS source_id,
                           target.id AS target_id
                    ORDER BY r.id
                    """,
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
                """
                MATCH (n:CodeIdempotency {
                    scope_key: $scope_key,
                    idempotency_key: $idempotency_key,
                    resource_type: $resource_type
                })
                RETURN n.resource_id AS resource_id
                """,
                scope_key=self._scope_key(scope),
                idempotency_key=key,
                resource_type=resource,
            ).single()
        return None if record is None else record["resource_id"]

    def complete_idempotency(self, scope: Scope, key: str, resource: str, resource_id: str) -> None:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                """
                MERGE (n:CodeIdempotency {
                    scope_key: $scope_key,
                    idempotency_key: $idempotency_key,
                    resource_type: $resource_type
                })
                ON CREATE SET n.resource_id = $resource_id
                RETURN n.resource_id AS resource_id
                """,
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
                """
                CREATE (n:CodeOutboxEvent {
                    event_id: $event_id,
                    event_type: $event_type,
                    payload_json: $payload_json,
                    created_at: datetime()
                })
                """,
                event_id=event["event_id"],
                event_type=event["event_type"],
                payload_json=json.dumps(event, sort_keys=True),
            )

    def outbox(self) -> list[dict[str, Any]]:
        with self._driver.session(database=self._database) as session:
            rows = list(
                session.run(
                    """
                    MATCH (n:CodeOutboxEvent)
                    RETURN n.payload_json AS payload_json
                    ORDER BY n.created_at, n.event_id
                    """
                )
            )
        return [json.loads(row["payload_json"]) for row in rows]
