from __future__ import annotations

from typing import Any

from . import _paths  # noqa: F401 — side effect: service path bootstrap
from . import docs, writes
from core_data_service.core import Kind

from .platform import PlatformBackends


def dispatch_capability(
    backends: PlatformBackends,
    maps_to: str,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    usage_profile: str,
    correlation_id: str,
) -> dict[str, Any]:
    base = {
        "maps_to": maps_to,
        "usage_profile": usage_profile,
        "scope": scope,
        "correlation_id": correlation_id,
        "backend": "in_process",
        "store_mode": backends.store_mode,
    }
    if maps_to == "platform.ping":
        return {**base, "ok": True}
    if maps_to == "profile.effective":
        return {**base, "ok": True}

    if maps_to == "memory.retrieve":
        return _memory_retrieve(backends, arguments, scope=scope, correlation_id=correlation_id, base=base)

    if maps_to == "code_graph.search":
        return _code_graph_search(backends, arguments, scope=scope, base=base)

    if maps_to == "core_data.create_task":
        return _create_task(backends, arguments, scope=scope, correlation_id=correlation_id, base=base)

    if maps_to == "platform.write":
        return writes.write_resource(
            backends, arguments, scope=scope, correlation_id=correlation_id, base=base
        )

    if maps_to == "docs_sync.drift_check":
        return docs.docs_drift_check(
            backends, arguments, scope=scope, correlation_id=correlation_id, base=base
        )

    if maps_to == "docs_sync.write":
        return docs.docs_write(
            backends, arguments, scope=scope, correlation_id=correlation_id, base=base
        )

    if maps_to == "docs_sync.status":
        return docs.docs_status(backends, scope=scope, base=base)

    raise ValueError(f"unmapped capability: {maps_to}")


def _memory_retrieve(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    query = str(arguments.get("query") or "").strip()
    if not query:
        raise ValueError("query is required")
    backends.ensure_memory_seed(scope, query)
    bundle = backends.memory.retrieve_context(
        backends.memory_scope(scope),
        backends.actor_id,
        correlation_id,
        query,
    )
    public = bundle.public()
    return {
        **base,
        "query": query,
        "include_history": bool(arguments.get("include_history", False)),
        "bundle_id": public.get("bundle_id"),
        "items": public.get("items") or [],
        "excluded": public.get("excluded") or [],
    }


def _code_graph_search(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    query = str(arguments.get("query") or "").strip()
    if not query:
        raise ValueError("query is required")
    top_k = int(arguments.get("top_k") or 5)
    backends.ensure_graph_seed(scope)
    hits = backends.graph.semantic_search(backends.graph_scope(scope), query, top_k=top_k)
    return {**base, "query": query, "top_k": top_k, "symbols": hits}


def _create_task(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    title = str(arguments.get("title") or "").strip()
    if not title:
        raise ValueError("title is required")
    instructions = str(arguments.get("instructions") or "Implement via AgentCore MCP task").strip()
    record = backends.core.create(
        Kind.TASK,
        backends.core_scope(scope),
        backends.actor_id,
        correlation_id,
        f"mcp-task:{correlation_id}",
        {
            "title": title,
            "assignee_type": "backend",
            "instructions": instructions,
            "acceptance_criteria": ["Implemented", "Tests pass"],
        },
    )
    return {**base, "task": record.public()}
