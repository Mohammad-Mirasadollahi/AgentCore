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


def _timestamp(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


class PostgresStore:
    """PostgreSQL adapter for the Code Graph Store port (graph projection + outbox)."""

    def __init__(self, database_url: str, *, ensure_schema: bool = True) -> None:
        if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("Code Graph database URL must use PostgreSQL")
        try:
            import psycopg
            from psycopg.rows import dict_row
            from psycopg.types.json import Jsonb
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("psycopg is required for PostgreSQL persistence") from exc
        normalized_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._connection = psycopg.connect(normalized_url, autocommit=True, row_factory=dict_row)
        self._json = Jsonb
        if ensure_schema:
            self.ensure_schema()

    def ensure_schema(self) -> None:
        """Apply core + FTS migrations when present."""
        from pathlib import Path

        migrations_dir = Path(__file__).resolve().parents[2] / "migrations"
        with self._connection.cursor() as cur:
            for name in ("0001_code_graph.sql", "0002_outbox_published.sql", "0006_symbol_fts.sql"):
                path = migrations_dir / name
                if path.is_file():
                    cur.execute(path.read_text(encoding="utf-8"))

    def capabilities(self) -> dict[str, bool]:
        return {"apoc": False, "gds": False, "fulltext": True}

    def fulltext_search(
        self,
        scope: Scope,
        query: str,
        *,
        top_k: int = 20,
    ) -> list[dict[str, Any]]:
        """Postgres FTS via tsvector / ts_rank_cd (english config)."""
        top_k = max(1, min(int(top_k), 100))
        q = (query or "").strip()
        if not q:
            return []
        with self._connection.cursor() as cur:
            cur.execute(
                """
                SELECT id AS symbol_id,
                       ts_rank_cd(
                         COALESCE(
                           search_document,
                           setweight(to_tsvector('english', coalesce(name, '')), 'A')
                           || setweight(to_tsvector('english', coalesce(qualified_name, '')), 'A')
                           || setweight(to_tsvector('english', coalesce(signature, '')), 'B')
                           || setweight(to_tsvector('english', coalesce(file_path, '')), 'B')
                           || setweight(to_tsvector('english', coalesce(ai_documentation, '')), 'C')
                         ),
                         plainto_tsquery('english', %s)
                       ) AS score
                FROM code_graph.symbols
                WHERE tenant_id = %s AND workspace_id = %s AND project_id = %s
                  AND (
                    COALESCE(search_document,
                      setweight(to_tsvector('english', coalesce(name, '')), 'A')
                      || setweight(to_tsvector('english', coalesce(qualified_name, '')), 'A')
                      || setweight(to_tsvector('english', coalesce(signature, '')), 'B')
                      || setweight(to_tsvector('english', coalesce(file_path, '')), 'B')
                      || setweight(to_tsvector('english', coalesce(ai_documentation, '')), 'C')
                    ) @@ plainto_tsquery('english', %s)
                  )
                ORDER BY score DESC, id
                LIMIT %s
                """,
                (q, scope.tenant_id, scope.workspace_id, scope.project_id, q, top_k),
            )
            rows = cur.fetchall()
        return [
            {
                "symbol_id": row["symbol_id"],
                "score": float(row["score"] or 0.0),
                "method": "postgres.fts",
            }
            for row in rows
            if float(row["score"] or 0.0) > 0
        ]

    @staticmethod
    def _scope_key(scope: Scope) -> str:
        return "|".join((scope.tenant_id, scope.workspace_id, scope.project_id, scope.project_group_id or ""))

    def _symbol(self, row: dict[str, Any], scope: Scope) -> GraphSymbol:
        return GraphSymbol(
            id=row["id"],
            scope=scope,
            kind=SymbolKind(row["kind"]),
            file_path=row["file_path"],
            name=row["name"],
            qualified_name=row["qualified_name"],
            signature=row["signature"],
            body=row["body"],
            hash_value=row["hash_value"],
            ai_documentation=row["ai_documentation"],
            doc_status=DocStatus(row["doc_status"]),
            embedding=list(row["embedding"] or []),
            visibility=row["visibility"],
            version=row["version"],
            created_at=_timestamp(row["created_at"]),
            updated_at=_timestamp(row["updated_at"]),
        )

    def get_symbol(self, symbol_id: str, scope: Scope) -> GraphSymbol:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM code_graph.symbols
                WHERE id = %s AND tenant_id = %s AND workspace_id = %s AND project_id = %s
                """,
                (symbol_id, scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            row = cur.fetchone()
        if row is None:
            raise NotFoundError("symbol not found in project scope")
        return self._symbol(row, scope)

    def put_symbol(self, symbol: GraphSymbol) -> None:
        scope = symbol.scope
        with self._connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO code_graph.symbols (
                    id, tenant_id, workspace_id, project_id, project_group_id, kind, file_path, name,
                    qualified_name, signature, body, hash_value, ai_documentation, doc_status, embedding,
                    visibility, version, created_at, updated_at
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                ON CONFLICT (id) DO UPDATE SET
                    kind = EXCLUDED.kind,
                    file_path = EXCLUDED.file_path,
                    name = EXCLUDED.name,
                    qualified_name = EXCLUDED.qualified_name,
                    signature = EXCLUDED.signature,
                    body = EXCLUDED.body,
                    hash_value = EXCLUDED.hash_value,
                    ai_documentation = EXCLUDED.ai_documentation,
                    doc_status = EXCLUDED.doc_status,
                    embedding = EXCLUDED.embedding,
                    visibility = EXCLUDED.visibility,
                    version = EXCLUDED.version,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    symbol.id,
                    scope.tenant_id,
                    scope.workspace_id,
                    scope.project_id,
                    scope.project_group_id,
                    symbol.kind.value,
                    symbol.file_path,
                    symbol.name,
                    symbol.qualified_name,
                    symbol.signature,
                    symbol.body,
                    symbol.hash_value,
                    symbol.ai_documentation,
                    symbol.doc_status.value,
                    self._json(symbol.embedding),
                    symbol.visibility,
                    symbol.version,
                    symbol.created_at,
                    symbol.updated_at,
                ),
            )
            # Refresh FTS document (column added by 0006_symbol_fts.sql).
            try:
                cur.execute(
                    """
                    UPDATE code_graph.symbols
                    SET search_document = (
                        setweight(to_tsvector('english', coalesce(name, '')), 'A')
                        || setweight(to_tsvector('english', coalesce(qualified_name, '')), 'A')
                        || setweight(to_tsvector('english', coalesce(signature, '')), 'B')
                        || setweight(to_tsvector('english', coalesce(file_path, '')), 'B')
                        || setweight(to_tsvector('english', coalesce(ai_documentation, '')), 'C')
                        || setweight(to_tsvector('english', left(coalesce(body, ''), 2000)), 'D')
                    )
                    WHERE id = %s
                    """,
                    (symbol.id,),
                )
            except Exception:
                pass

    def list_symbols(self, scope: Scope) -> list[GraphSymbol]:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM code_graph.symbols
                WHERE tenant_id = %s AND workspace_id = %s AND project_id = %s
                ORDER BY qualified_name, id
                """,
                (scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            rows = cur.fetchall()
        return [self._symbol(row, scope) for row in rows]

    def get_symbol_by_qualified_name(self, scope: Scope, qualified_name: str) -> GraphSymbol | None:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM code_graph.symbols
                WHERE tenant_id = %s AND workspace_id = %s AND project_id = %s AND qualified_name = %s
                """,
                (scope.tenant_id, scope.workspace_id, scope.project_id, qualified_name),
            )
            row = cur.fetchone()
        return None if row is None else self._symbol(row, scope)

    def delete_file_edges(self, scope: Scope, file_path: str) -> None:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                DELETE FROM code_graph.edges
                WHERE tenant_id = %s AND workspace_id = %s AND project_id = %s
                  AND metadata->>'file_path' = %s
                """,
                (scope.tenant_id, scope.workspace_id, scope.project_id, file_path),
            )

    def delete_edge(self, scope: Scope, edge_id: str) -> None:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                DELETE FROM code_graph.edges
                WHERE id = %s AND tenant_id = %s AND workspace_id = %s AND project_id = %s
                """,
                (edge_id, scope.tenant_id, scope.workspace_id, scope.project_id),
            )

    def put_edge(self, edge: GraphEdge) -> None:
        scope = edge.scope
        with self._connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO code_graph.edges (
                    id, tenant_id, workspace_id, project_id, project_group_id, rel_type, source_id,
                    target_id, confidence, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                    rel_type = EXCLUDED.rel_type,
                    source_id = EXCLUDED.source_id,
                    target_id = EXCLUDED.target_id,
                    confidence = EXCLUDED.confidence,
                    metadata = EXCLUDED.metadata
                """,
                (
                    edge.id,
                    scope.tenant_id,
                    scope.workspace_id,
                    scope.project_id,
                    scope.project_group_id,
                    edge.rel_type,
                    edge.source_id,
                    edge.target_id,
                    edge.confidence.value,
                    self._json(edge.metadata),
                ),
            )

    def list_edges(self, scope: Scope) -> list[GraphEdge]:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM code_graph.edges
                WHERE tenant_id = %s AND workspace_id = %s AND project_id = %s
                ORDER BY id
                """,
                (scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            rows = cur.fetchall()
        return [
            GraphEdge(
                id=row["id"],
                scope=scope,
                rel_type=row["rel_type"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                confidence=CallConfidence(row["confidence"]),
                metadata=dict(row["metadata"] or {}),
            )
            for row in rows
        ]

    def begin_idempotency(self, scope: Scope, key: str, resource: str) -> str | None:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                SELECT resource_id FROM code_graph.idempotency
                WHERE scope_key = %s AND idempotency_key = %s AND resource_type = %s
                """,
                (self._scope_key(scope), key, resource),
            )
            row = cur.fetchone()
        return None if row is None else row["resource_id"]

    def complete_idempotency(self, scope: Scope, key: str, resource: str, resource_id: str) -> None:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO code_graph.idempotency (scope_key, idempotency_key, resource_type, resource_id)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (scope_key, idempotency_key, resource_type) DO UPDATE
                SET resource_id = EXCLUDED.resource_id
                RETURNING resource_id
                """,
                (self._scope_key(scope), key, resource, resource_id),
            )
            row = cur.fetchone()
        if row and row["resource_id"] != resource_id:
            raise ConflictError("idempotency key already bound to another resource")

    def append_event(self, event: dict[str, Any]) -> None:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO code_graph.outbox (event_id, event_type, payload)
                VALUES (%s,%s,%s)
                """,
                (event["event_id"], event["event_type"], self._json(event)),
            )

    def outbox(self) -> list[dict[str, Any]]:
        with self._connection.cursor() as cur:
            cur.execute("SELECT payload FROM code_graph.outbox ORDER BY created_at, event_id")
            rows = cur.fetchall()
        return [dict(row["payload"]) if isinstance(row["payload"], dict) else json.loads(row["payload"]) for row in rows]
