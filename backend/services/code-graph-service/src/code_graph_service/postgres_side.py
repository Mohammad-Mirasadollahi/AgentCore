"""PostgreSQL pgvector index for code-graph semantic retrieval (Stage-1 hybrid RAG)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, Sequence

from .domain.models import Scope
from .domain.rag import SEARCHABLE_SYMBOL_KINDS


class EmbeddingIndex(Protocol):
    def upsert(
        self,
        scope: Scope,
        symbol_id: str,
        vector: list[float],
        *,
        model: str,
        kind: str = "unknown",
    ) -> None: ...

    def delete(self, scope: Scope, symbol_id: str) -> None: ...

    def search(
        self,
        scope: Scope,
        vector: list[float],
        *,
        top_k: int = 5,
        kinds: Sequence[str] | None = None,
    ) -> list[tuple[str, float]]: ...


class InMemoryEmbeddingIndex:
    """Test double for EmbeddingIndex."""

    def __init__(self) -> None:
        # key → (vector, model, kind)
        self._rows: dict[tuple[str, str, str, str], tuple[list[float], str, str]] = {}

    def upsert(
        self,
        scope: Scope,
        symbol_id: str,
        vector: list[float],
        *,
        model: str,
        kind: str = "unknown",
    ) -> None:
        key = (scope.tenant_id, scope.workspace_id, scope.project_id, symbol_id)
        self._rows[key] = (list(vector), model, str(kind or "unknown"))

    def delete(self, scope: Scope, symbol_id: str) -> None:
        key = (scope.tenant_id, scope.workspace_id, scope.project_id, symbol_id)
        self._rows.pop(key, None)

    def wipe_scope(self, scope: Scope) -> int:
        drop = [
            key
            for key in self._rows
            if key[:3] == (scope.tenant_id, scope.workspace_id, scope.project_id)
        ]
        for key in drop:
            del self._rows[key]
        return len(drop)

    def list_symbol_models(self, scope: Scope) -> dict[str, str]:
        """Return symbol_id → embedding model for one scope."""
        out: dict[str, str] = {}
        for (tenant, workspace, project, symbol_id), (_vec, model, _kind) in self._rows.items():
            if (tenant, workspace, project) != (scope.tenant_id, scope.workspace_id, scope.project_id):
                continue
            if model:
                out[symbol_id] = str(model)
        return out

    def search(
        self,
        scope: Scope,
        vector: list[float],
        *,
        top_k: int = 5,
        kinds: Sequence[str] | None = None,
    ) -> list[tuple[str, float]]:
        from code_graph_service.domain.embeddings import cosine

        allowed = {str(k) for k in (kinds if kinds is not None else SEARCHABLE_SYMBOL_KINDS)}
        scored: list[tuple[str, float]] = []
        for (tenant, workspace, project, symbol_id), (stored, _model, kind) in self._rows.items():
            if (tenant, workspace, project) != (scope.tenant_id, scope.workspace_id, scope.project_id):
                continue
            if allowed and kind not in allowed:
                continue
            scored.append((symbol_id, cosine(vector, stored)))
        scored.sort(key=lambda item: (-item[1], item[0]))
        return [(sid, score) for sid, score in scored[: max(1, top_k)] if score > 0]


class PostgresEmbeddingIndex:
    """pgvector-backed ANN index (cosine distance) for symbol embeddings."""

    def __init__(self, database_url: str, *, dims: int = 1024, ensure_schema: bool = True) -> None:
        if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("Embedding index database URL must use PostgreSQL")
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("psycopg is required for PostgresEmbeddingIndex") from exc
        normalized = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._dims = dims
        self._connection = psycopg.connect(normalized, autocommit=True, row_factory=dict_row)
        if ensure_schema:
            self.ensure_schema()

    def close(self) -> None:
        self._connection.close()

    def ensure_schema(self) -> None:
        migrations_dir = Path(__file__).resolve().parents[2] / "migrations"
        with self._connection.cursor() as cur:
            for name in (
                "0003_symbol_embeddings.sql",
                "0004_symbol_embeddings_kind.sql",
                "0005_symbol_embeddings_dims_1024.sql",
            ):
                path = migrations_dir / name
                if path.is_file():
                    cur.execute(path.read_text(encoding="utf-8"))
            # If an older vector(16) table still exists, rebuild to match configured dims.
            cur.execute(
                """
                SELECT format_type(a.atttypid, a.atttypmod) AS typ
                FROM pg_attribute a
                JOIN pg_class c ON c.oid = a.attrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'code_graph'
                  AND c.relname = 'symbol_embeddings'
                  AND a.attname = 'embedding'
                  AND a.attnum > 0
                  AND NOT a.attisdropped
                """
            )
            row = cur.fetchone()
            expected = f"vector({self._dims})"
            if row and str(row.get("typ") or "") != expected:
                cur.execute("DROP TABLE IF EXISTS code_graph.symbol_embeddings CASCADE")
                cur.execute(
                    f"""
                    CREATE TABLE code_graph.symbol_embeddings (
                        symbol_id text PRIMARY KEY,
                        tenant_id text NOT NULL,
                        workspace_id text NOT NULL,
                        project_id text NOT NULL,
                        model text NOT NULL,
                        dims integer NOT NULL CHECK (dims > 0),
                        kind text NOT NULL DEFAULT 'unknown',
                        embedding vector({self._dims}) NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX code_graph_symbol_embeddings_scope_idx
                        ON code_graph.symbol_embeddings (tenant_id, workspace_id, project_id)
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX code_graph_symbol_embeddings_scope_kind_idx
                        ON code_graph.symbol_embeddings (tenant_id, workspace_id, project_id, kind)
                    """
                )
                cur.execute(
                    f"""
                    CREATE INDEX code_graph_symbol_embeddings_hnsw_idx
                        ON code_graph.symbol_embeddings
                        USING hnsw (embedding vector_cosine_ops)
                    """
                )

    @staticmethod
    def _vector_literal(vector: list[float]) -> str:
        return "[" + ",".join(str(float(v)) for v in vector) + "]"

    def upsert(
        self,
        scope: Scope,
        symbol_id: str,
        vector: list[float],
        *,
        model: str,
        kind: str = "unknown",
    ) -> None:
        if len(vector) != self._dims:
            raise ValueError(f"embedding dims must be {self._dims}, got {len(vector)}")
        literal = self._vector_literal(vector)
        kind_value = str(kind or "unknown").strip() or "unknown"
        with self._connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO code_graph.symbol_embeddings (
                    symbol_id, tenant_id, workspace_id, project_id, model, dims, kind, embedding, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s::vector, now()
                )
                ON CONFLICT (symbol_id) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    workspace_id = EXCLUDED.workspace_id,
                    project_id = EXCLUDED.project_id,
                    model = EXCLUDED.model,
                    dims = EXCLUDED.dims,
                    kind = EXCLUDED.kind,
                    embedding = EXCLUDED.embedding,
                    updated_at = now()
                """,
                (
                    symbol_id,
                    scope.tenant_id,
                    scope.workspace_id,
                    scope.project_id,
                    model,
                    self._dims,
                    kind_value,
                    literal,
                ),
            )

    def delete(self, scope: Scope, symbol_id: str) -> None:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                DELETE FROM code_graph.symbol_embeddings
                WHERE symbol_id = %s
                  AND tenant_id = %s
                  AND workspace_id = %s
                  AND project_id = %s
                """,
                (symbol_id, scope.tenant_id, scope.workspace_id, scope.project_id),
            )

    def wipe_scope(self, scope: Scope) -> int:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                DELETE FROM code_graph.symbol_embeddings
                WHERE tenant_id = %s AND workspace_id = %s AND project_id = %s
                """,
                (scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            return int(cur.rowcount or 0)

    def list_symbol_models(self, scope: Scope) -> dict[str, str]:
        """Return symbol_id → embedding model for one scope."""
        with self._connection.cursor() as cur:
            cur.execute(
                """
                SELECT symbol_id, model
                FROM code_graph.symbol_embeddings
                WHERE tenant_id = %s AND workspace_id = %s AND project_id = %s
                """,
                (scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            rows = cur.fetchall() or []
        out: dict[str, str] = {}
        for row in rows:
            sid = str(row.get("symbol_id") or "").strip()
            model = str(row.get("model") or "").strip()
            if sid and model:
                out[sid] = model
        return out

    def search(
        self,
        scope: Scope,
        vector: list[float],
        *,
        top_k: int = 5,
        kinds: Sequence[str] | None = None,
    ) -> list[tuple[str, float]]:
        if len(vector) != self._dims:
            raise ValueError(f"query dims must be {self._dims}, got {len(vector)}")
        literal = self._vector_literal(vector)
        allowed = [str(k) for k in (kinds if kinds is not None else SEARCHABLE_SYMBOL_KINDS)]
        with self._connection.cursor() as cur:
            cur.execute(
                """
                SELECT symbol_id,
                       1 - (embedding <=> %s::vector) AS score
                FROM code_graph.symbol_embeddings
                WHERE tenant_id = %s
                  AND workspace_id = %s
                  AND project_id = %s
                  AND kind = ANY(%s)
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    literal,
                    scope.tenant_id,
                    scope.workspace_id,
                    scope.project_id,
                    allowed,
                    literal,
                    max(1, top_k),
                ),
            )
            rows = cur.fetchall()
        return [(str(row["symbol_id"]), float(row["score"])) for row in rows if float(row["score"]) > 0]


class PostgresOutboxMirror:
    """Writes code-graph outbox rows so the Postgres outbox-relay can publish Neo4j events."""

    def __init__(self, database_url: str) -> None:
        if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("Outbox mirror database URL must use PostgreSQL")
        try:
            import psycopg
            from psycopg.rows import dict_row
            from psycopg.types.json import Jsonb
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("psycopg is required for PostgresOutboxMirror") from exc
        normalized = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._connection = psycopg.connect(normalized, autocommit=True, row_factory=dict_row)
        self._json = Jsonb

    def close(self) -> None:
        self._connection.close()

    def append_event(self, event: dict[str, Any]) -> None:
        with self._connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO code_graph.outbox (event_id, event_type, payload)
                VALUES (%s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (event["event_id"], event["event_type"], self._json(event)),
            )
