"""Build in-process service stores for the MCP gateway (memory or PostgreSQL)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

StoreMode = Literal["memory", "postgres"]

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
    core: Any
    memory: Any
    graph: Any
    docs: Any
    common_context: Any
    database_url: str | None = None

    def close(self) -> None:
        for store in (self.core, self.memory, self.graph, self.docs, self.common_context):
            closer = getattr(store, "close", None)
            if callable(closer):
                closer()


def resolve_store_mode(environ: dict[str, str] | None = None) -> StoreMode:
    env = environ if environ is not None else os.environ
    explicit = str(env.get("AGENTCORE_MCP_STORE_MODE") or "").strip().lower()
    if explicit in {"memory", "postgres"}:
        return explicit  # type: ignore[return-value]
    if _shared_or_any_url(env):
        return "postgres"
    return "memory"


def _shared_or_any_url(env: dict[str, str]) -> str | None:
    shared = str(env.get("AGENTCORE_DATABASE_URL") or "").strip()
    if shared:
        return shared
    for key in SERVICE_URL_ENV.values():
        value = str(env.get(key) or "").strip()
        if value:
            return value
    return None


def _url_for(service: str, env: dict[str, str]) -> str:
    specific = str(env.get(SERVICE_URL_ENV[service]) or "").strip()
    if specific:
        return specific
    shared = str(env.get("AGENTCORE_DATABASE_URL") or "").strip()
    if shared:
        return shared
    raise ValueError(
        f"postgres store mode requires AGENTCORE_DATABASE_URL or {SERVICE_URL_ENV[service]}"
    )


def build_stores(environ: dict[str, str] | None = None) -> StoreBundle:
    env = environ if environ is not None else os.environ
    mode = resolve_store_mode(env)
    if mode == "memory":
        from code_graph_service.testing import InMemoryStore as GraphStore
        from common_context_service.testing import InMemoryStore as CommonContextStore
        from core_data_service.testing import InMemoryStore as CoreStore
        from docs_sync_service.testing import InMemoryStore as DocsStore
        from memory_service.testing import InMemoryStore as MemoryStore

        return StoreBundle(
            mode="memory",
            core=CoreStore(),
            memory=MemoryStore(),
            graph=GraphStore(),
            docs=DocsStore(),
            common_context=CommonContextStore(),
        )

    from code_graph_service.postgres_store import PostgresStore as GraphStore
    from common_context_service.postgres_store import PostgresStore as CommonContextStore
    from core_data_service.postgres_store import PostgresStore as CoreStore
    from docs_sync_service.postgres_store import PostgresStore as DocsStore
    from memory_service.postgres_store import PostgresStore as MemoryStore

    urls = {name: _url_for(name, env) for name in SERVICE_URL_ENV}
    return StoreBundle(
        mode="postgres",
        core=CoreStore(urls["core"]),
        memory=MemoryStore(urls["memory"]),
        graph=GraphStore(urls["graph"]),
        docs=DocsStore(urls["docs"]),
        common_context=CommonContextStore(urls["common_context"]),
        database_url=urls["core"],
    )
