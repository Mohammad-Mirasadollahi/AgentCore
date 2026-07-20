from __future__ import annotations

from dataclasses import dataclass
import os

from .core import CodeGraphService
from .llm_wiring import LlmBackedDocGenerator, build_embeddings
from .local_embeddings import embedding_settings_from_env
from .neo4j_store import Neo4jStore
from .outbox_mirror_store import OutboxMirrorStore
from .postgres_side import PostgresEmbeddingIndex, PostgresOutboxMirror
from .postgres_store import PostgresStore


@dataclass(frozen=True)
class Settings:
    store_backend: str
    database_url: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str
    neo4j_gds_enabled: bool = True
    neo4j_gds_concurrency: int = 4

    @classmethod
    def from_environment(cls, environ: dict[str, str] | None = None) -> "Settings":
        # Neo4j is the default structural store (GAP-011 closed). Postgres remains
        # available via AGENTCORE_CODE_GRAPH_STORE=postgres for rollback / parity.
        # AGENTCORE_CODE_GRAPH_DATABASE_URL enables pgvector embeddings + outbox mirror.
        env = environ if environ is not None else os.environ
        store_backend = str(env.get("AGENTCORE_CODE_GRAPH_STORE", "neo4j")).strip().lower() or "neo4j"
        if store_backend not in {"postgres", "neo4j"}:
            raise RuntimeError("AGENTCORE_CODE_GRAPH_STORE must be 'postgres' or 'neo4j'")

        database_url = str(env.get("AGENTCORE_CODE_GRAPH_DATABASE_URL", "")).strip()
        neo4j_uri = str(env.get("AGENTCORE_NEO4J_URI", "bolt://127.0.0.1:32287")).strip() or "bolt://127.0.0.1:32287"
        neo4j_user = str(env.get("AGENTCORE_NEO4J_USER", "neo4j")).strip() or "neo4j"
        neo4j_password = str(env.get("AGENTCORE_NEO4J_PASSWORD", "")).strip()
        neo4j_database = str(env.get("AGENTCORE_NEO4J_DATABASE", "neo4j")).strip() or "neo4j"
        neo4j_gds_enabled = _env_flag(env.get("AGENTCORE_NEO4J_GDS_ENABLED"), default=True)
        neo4j_gds_concurrency = _gds_concurrency(env.get("AGENTCORE_NEO4J_GDS_CONCURRENCY"))

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
            if database_url and not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
                raise RuntimeError("AGENTCORE_CODE_GRAPH_DATABASE_URL must use PostgreSQL when set")

        return cls(
            store_backend=store_backend,
            database_url=database_url,
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            neo4j_database=neo4j_database,
            neo4j_gds_enabled=neo4j_gds_enabled,
            neo4j_gds_concurrency=neo4j_gds_concurrency,
        )


def _env_flag(raw: str | None, *, default: bool) -> bool:
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() not in {"0", "false", "no", "off"}


def _gds_concurrency(raw: str | None) -> int:
    """GDS Community Edition caps concurrency at 4 cores — never exceed."""
    try:
        value = int(str(raw).strip() or "4")
    except ValueError:
        value = 4
    return max(1, min(value, 4))


def build_store(settings: Settings):
    if settings.store_backend == "neo4j":
        store = Neo4jStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
            gds_enabled=settings.neo4j_gds_enabled,
            gds_concurrency=settings.neo4j_gds_concurrency,
        )
        if settings.database_url:
            return OutboxMirrorStore(store, PostgresOutboxMirror(settings.database_url))
        return store
    return PostgresStore(settings.database_url)


def build_embedding_index(settings: Settings) -> PostgresEmbeddingIndex | None:
    if not settings.database_url:
        return None
    dims = int(embedding_settings_from_env()["dims"])
    return PostgresEmbeddingIndex(settings.database_url, dims=dims, ensure_schema=True)


def build_llm_gateway():
    """Construct the shared LiteLLM gateway from environment."""
    from llm_gateway import LiteLlmGateway, LlmGatewaySettings

    return LiteLlmGateway(LlmGatewaySettings.from_environment())


def build_service(settings: Settings | None = None) -> CodeGraphService:
    resolved = settings or Settings.from_environment()
    gateway = build_llm_gateway()
    embeddings = build_embeddings(gateway, settings=gateway.settings)
    return CodeGraphService(
        build_store(resolved),
        docs=LlmBackedDocGenerator(gateway, settings=gateway.settings),
        embeddings=embeddings,
        embedding_index=build_embedding_index(resolved),
        llm=gateway,
    )
