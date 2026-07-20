"""Build in-process service stores for the MCP gateway (memory, PostgreSQL, or Neo4j graph)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal, Mapping

StoreMode = Literal["memory", "postgres"]
GraphMode = Literal["memory", "postgres", "neo4j"]

SERVICE_URL_ENV = {
    "core": "AGENTCORE_CORE_DATA_DATABASE_URL",
    "memory": "AGENTCORE_MEMORY_DATABASE_URL",
    "graph": "AGENTCORE_CODE_GRAPH_DATABASE_URL",
    "docs": "AGENTCORE_DOCS_SYNC_DATABASE_URL",
    "common_context": "AGENTCORE_COMMON_CONTEXT_DATABASE_URL",
}


@dataclass(frozen=True)
class StoreBundle:
    mode: StoreMode
    graph_mode: GraphMode
    core: Any
    memory: Any
    graph: Any
    docs: Any
    common_context: Any
    database_url: str | None = None
    # When graph_mode == neo4j, graph is unused; graph_service is the live facade.
    graph_service: Any | None = None

    def close(self) -> None:
        if self.graph_service is not None:
            closer = getattr(self.graph_service.store, "close", None)
            if callable(closer):
                closer()
        for store in (self.core, self.memory, self.graph, self.docs, self.common_context):
            if store is None:
                continue
            closer = getattr(store, "close", None)
            if callable(closer):
                closer()


def resolve_store_mode(environ: Mapping[str, str] | None = None) -> StoreMode:
    env = environ if environ is not None else os.environ
    explicit = str(env.get("AGENTCORE_MCP_STORE_MODE") or "").strip().lower()
    if explicit in {"memory", "postgres"}:
        return explicit  # type: ignore[return-value]
    # Only the shared platform URL implies postgres for all MCP companion stores.
    # A lone AGENTCORE_CODE_GRAPH_DATABASE_URL must not force core/memory onto postgres.
    if str(env.get("AGENTCORE_DATABASE_URL") or "").strip():
        return "postgres"
    return "memory"


def resolve_graph_mode(environ: Mapping[str, str] | None = None) -> GraphMode:
    """Select code-graph backend for MCP (independent of other service store mode).

    Priority:
    1. AGENTCORE_MCP_GRAPH_MODE = memory|postgres|neo4j
    2. auto: Neo4j when password is set and CODE_GRAPH_STORE is neo4j (default)
    3. else follow AGENTCORE_MCP_STORE_MODE / postgres URL detection
    """
    env = environ if environ is not None else os.environ
    explicit = str(env.get("AGENTCORE_MCP_GRAPH_MODE") or "").strip().lower()
    if explicit in {"memory", "postgres", "neo4j"}:
        return explicit  # type: ignore[return-value]

    store_backend = str(env.get("AGENTCORE_CODE_GRAPH_STORE", "neo4j")).strip().lower() or "neo4j"
    neo4j_password = str(env.get("AGENTCORE_NEO4J_PASSWORD") or "").strip()
    placeholder_passwords = {
        "",
        "replace-with-a-local-secret",
        "changeme",
        "password",
        "neo4j",
    }
    if store_backend == "neo4j" and neo4j_password and neo4j_password not in placeholder_passwords:
        return "neo4j"
    if store_backend == "postgres":
        return "postgres"
    return resolve_store_mode(env)


def _url_for(service: str, env: Mapping[str, str]) -> str:
    specific = str(env.get(SERVICE_URL_ENV[service]) or "").strip()
    if specific:
        return specific
    shared = str(env.get("AGENTCORE_DATABASE_URL") or "").strip()
    if shared:
        return shared
    raise ValueError(
        f"postgres store mode requires AGENTCORE_DATABASE_URL or {SERVICE_URL_ENV[service]}"
    )


def _env_dict(environ: Mapping[str, str] | None) -> dict[str, str]:
    if environ is None:
        return dict(os.environ)
    return {str(k): str(v) for k, v in environ.items()}


def build_stores(environ: Mapping[str, str] | None = None) -> StoreBundle:
    env = _env_dict(environ)
    mode = resolve_store_mode(env)
    graph_mode = resolve_graph_mode(env)

    if mode == "memory":
        from common_context_service.testing import InMemoryStore as CommonContextStore
        from core_data_service.testing import InMemoryStore as CoreStore
        from docs_sync_service.testing import InMemoryStore as DocsStore
        from memory_service.testing import InMemoryStore as MemoryStore

        core, memory, docs, common_context = (
            CoreStore(),
            MemoryStore(),
            DocsStore(),
            CommonContextStore(),
        )
        database_url = None
    else:
        from common_context_service.postgres_store import PostgresStore as CommonContextStore
        from core_data_service.postgres_store import PostgresStore as CoreStore
        from docs_sync_service.postgres_store import PostgresStore as DocsStore
        from memory_service.postgres_store import PostgresStore as MemoryStore

        urls = {name: _url_for(name, env) for name in SERVICE_URL_ENV}
        core = CoreStore(urls["core"])
        memory = MemoryStore(urls["memory"])
        docs = DocsStore(urls["docs"])
        common_context = CommonContextStore(urls["common_context"])
        database_url = urls["core"]

    graph_service = None
    graph_store: Any = None

    if graph_mode == "neo4j":
        from code_graph_service.bootstrap import Settings, build_service

        graph_service = build_service(Settings.from_environment(env))
        # Placeholder unused store so close() loops stay simple; real close via graph_service.
        from code_graph_service.testing import InMemoryStore as GraphStore

        graph_store = GraphStore()
    elif graph_mode == "postgres":
        from code_graph_service.postgres_store import PostgresStore as GraphStore

        graph_store = GraphStore(_url_for("graph", env))
    else:
        from code_graph_service.testing import InMemoryStore as GraphStore

        graph_store = GraphStore()

    return StoreBundle(
        mode=mode,
        graph_mode=graph_mode,
        core=core,
        memory=memory,
        graph=graph_store,
        docs=docs,
        common_context=common_context,
        database_url=database_url,
        graph_service=graph_service,
    )
