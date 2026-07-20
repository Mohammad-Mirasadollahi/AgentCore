from __future__ import annotations

from dataclasses import dataclass
import os

from .core import CodeGraphService
from .neo4j_store import Neo4jStore
from .postgres_store import PostgresStore


@dataclass(frozen=True)
class Settings:
    store_backend: str
    database_url: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str

    @classmethod
    def from_environment(cls) -> "Settings":
        store_backend = os.environ.get("AGENTCORE_CODE_GRAPH_STORE", "postgres").strip().lower() or "postgres"
        if store_backend not in {"postgres", "neo4j"}:
            raise RuntimeError("AGENTCORE_CODE_GRAPH_STORE must be 'postgres' or 'neo4j'")

        database_url = os.environ.get("AGENTCORE_CODE_GRAPH_DATABASE_URL", "").strip()
        neo4j_uri = os.environ.get("AGENTCORE_NEO4J_URI", "").strip()
        neo4j_user = os.environ.get("AGENTCORE_NEO4J_USER", "neo4j").strip() or "neo4j"
        neo4j_password = os.environ.get("AGENTCORE_NEO4J_PASSWORD", "").strip()
        neo4j_database = os.environ.get("AGENTCORE_NEO4J_DATABASE", "neo4j").strip() or "neo4j"

        if store_backend == "postgres":
            if not database_url:
                raise RuntimeError("AGENTCORE_CODE_GRAPH_DATABASE_URL is required for postgres store")
            if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
                raise RuntimeError("AGENTCORE_CODE_GRAPH_DATABASE_URL must use PostgreSQL")
        else:
            if not neo4j_uri:
                raise RuntimeError("AGENTCORE_NEO4J_URI is required for neo4j store")
            if not neo4j_password:
                raise RuntimeError("AGENTCORE_NEO4J_PASSWORD is required for neo4j store")

        return cls(
            store_backend=store_backend,
            database_url=database_url,
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            neo4j_database=neo4j_database,
        )


def build_store(settings: Settings):
    if settings.store_backend == "neo4j":
        return Neo4jStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
    return PostgresStore(settings.database_url)


def build_service(settings: Settings | None = None) -> CodeGraphService:
    resolved = settings or Settings.from_environment()
    return CodeGraphService(build_store(resolved))
