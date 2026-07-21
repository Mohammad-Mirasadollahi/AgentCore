"""MCP write handlers: ingest, sync, purge."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from code_graph_service.domain.errors import CodeGraphError, NotFoundError

from ..platform import PlatformBackends

def ingest_file(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    file_path = str(arguments.get("file_path") or "").strip()
    source = str(arguments.get("source") or "")
    language = str(arguments.get("language") or "python").strip() or "python"
    if not file_path:
        raise ValueError("file_path is required")
    if not source.strip():
        raise ValueError("source is required")
    idempotency_key = str(arguments.get("idempotency_key") or f"mcp-ingest:{file_path}:{correlation_id}").strip()
    try:
        result = backends.graph.ingest_file(
            backends.graph_scope(scope),
            backends.actor_id,
            correlation_id or str(uuid4()),
            idempotency_key,
            {
                "file_path": file_path,
                "language": language,
                "source": source,
            },
        )
    except CodeGraphError as exc:
        raise ValueError(str(exc.message)) from exc
    if hasattr(result, "public"):
        public = result.public()
    else:
        public = {
            "file_id": result.file_id,
            "symbols_indexed": result.symbols_indexed,
            "symbols_changed": result.symbols_changed,
            "symbols_documented": result.symbols_documented,
            "edges_written": result.edges_written,
            "changed_symbol_ids": list(result.changed_symbol_ids),
        }
    return {
        **base,
        "graph_mode": backends.graph_mode,
        "ingest": public,
    }


def ingest_repo(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    root_path = str(arguments.get("root_path") or "").strip()
    if not root_path:
        raise ValueError("root_path is required")
    payload: dict[str, Any] = {"root_path": root_path}
    if arguments.get("include_extensions") is not None:
        payload["include_extensions"] = arguments.get("include_extensions")
    if arguments.get("exclude_dirs") is not None:
        payload["exclude_dirs"] = arguments.get("exclude_dirs")
    if arguments.get("max_files") is not None:
        payload["max_files"] = int(arguments["max_files"])
    if arguments.get("max_file_bytes") is not None:
        payload["max_file_bytes"] = int(arguments["max_file_bytes"])
    if "include_outcomes" in arguments:
        payload["include_outcomes"] = bool(arguments.get("include_outcomes"))
    idempotency_key = str(
        arguments.get("idempotency_key") or f"mcp-ingest-repo:{root_path}:{correlation_id}"
    ).strip()
    try:
        result = backends.graph.ingest_repo(
            backends.graph_scope(scope),
            backends.actor_id,
            correlation_id or str(uuid4()),
            idempotency_key,
            payload,
        )
    except CodeGraphError as exc:
        raise ValueError(str(exc.message)) from exc
    return {
        **base,
        "graph_mode": backends.graph_mode,
        "ingest_repo": result.to_dict(),
    }


def sync_repo(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    root_path = str(arguments.get("root_path") or "").strip()
    if not root_path:
        raise ValueError("root_path is required")
    payload: dict[str, Any] = {"root_path": root_path, "include_outcomes": True}
    if arguments.get("max_files") is not None:
        payload["max_files"] = int(arguments["max_files"])
    if arguments.get("include_extensions") is not None:
        payload["include_extensions"] = arguments.get("include_extensions")
    idempotency_key = str(
        arguments.get("idempotency_key") or f"mcp-sync:{root_path}:{correlation_id}"
    ).strip()
    try:
        result = backends.graph.sync_repo(
            backends.graph_scope(scope),
            backends.actor_id,
            correlation_id or str(uuid4()),
            idempotency_key,
            payload,
        )
    except CodeGraphError as exc:
        raise ValueError(str(exc.message)) from exc
    return {
        **base,
        "graph_mode": backends.graph_mode,
        "sync": result.to_dict(),
    }


def purge_scope(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    if not bool(arguments.get("confirm")):
        raise ValueError("purge requires confirm=true")
    try:
        result = backends.graph.purge_scope(backends.graph_scope(scope))
    except CodeGraphError as exc:
        raise ValueError(str(exc.message)) from exc
    return {**base, "graph_mode": backends.graph_mode, "purge": result}


