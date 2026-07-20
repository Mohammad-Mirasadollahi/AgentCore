"""MCP capability handlers for the code-knowledge graph."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from code_graph_service.domain.errors import CodeGraphError, NotFoundError

from .platform import PlatformBackends


def _resolve_symbol_id(backends: PlatformBackends, scope: dict[str, str], arguments: dict[str, Any]) -> str:
    symbol_id = str(arguments.get("symbol_id") or "").strip()
    if symbol_id:
        return symbol_id
    qualified = str(arguments.get("qualified_name") or arguments.get("name") or "").strip()
    if not qualified:
        raise ValueError("symbol_id or qualified_name is required")
    graph_scope = backends.graph_scope(scope)
    matches: list[str] = []
    for symbol in backends.graph.store.list_symbols(graph_scope):
        if symbol.qualified_name == qualified or symbol.name == qualified:
            matches.append(symbol.id)
    if not matches:
        raise ValueError(f"symbol not found for qualified_name/name={qualified!r}")
    if len(matches) > 1:
        # Prefer exact qualified_name match order already collected; return first stable id.
        return matches[0]
    return matches[0]


def search(
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
    return {
        **base,
        "query": query,
        "top_k": top_k,
        "graph_mode": backends.graph_mode,
        "symbols": hits,
    }


def get_symbol(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    backends.ensure_graph_seed(scope)
    symbol_id = _resolve_symbol_id(backends, scope, arguments)
    try:
        symbol = backends.graph.get_symbol(backends.graph_scope(scope), symbol_id)
    except NotFoundError as exc:
        raise ValueError(str(exc.message)) from exc
    view = backends.graph._symbol_view(symbol)  # noqa: SLF001 — shared public view helper
    return {**base, "graph_mode": backends.graph_mode, "symbol": view}


def neighbors(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    backends.ensure_graph_seed(scope)
    symbol_id = _resolve_symbol_id(backends, scope, arguments)
    rel_type = str(arguments.get("rel_type") or "").strip() or None
    max_depth = int(arguments.get("max_depth") or 1)
    max_depth = max(1, min(max_depth, 8))
    try:
        payload = backends.graph.structural_query(
            backends.graph_scope(scope),
            symbol_id,
            rel_type,
            max_depth=max_depth,
        )
    except NotFoundError as exc:
        raise ValueError(str(exc.message)) from exc
    return {**base, "graph_mode": backends.graph_mode, **payload}


def impact(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    """Impact-style neighborhood: multi-hop structural expand around a seed symbol."""
    backends.ensure_graph_seed(scope)
    symbol_id = _resolve_symbol_id(backends, scope, arguments)
    rel_type = str(arguments.get("rel_type") or "").strip() or None
    max_depth = int(arguments.get("max_depth") or 3)
    max_depth = max(1, min(max_depth, 8))
    try:
        payload = backends.graph.structural_query(
            backends.graph_scope(scope),
            symbol_id,
            rel_type,
            max_depth=max_depth,
        )
    except NotFoundError as exc:
        raise ValueError(str(exc.message)) from exc
    return {
        **base,
        "graph_mode": backends.graph_mode,
        "impact_of": symbol_id,
        **payload,
    }


def explore(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    """Primary surgical context tool: query → seeds + call path + budgeted bodies."""
    query = str(arguments.get("query") or "").strip()
    if not query:
        raise ValueError("query is required")
    top_k = int(arguments.get("top_k") or 12)
    max_depth = int(arguments.get("max_depth") or 2)
    budget = arguments.get("budget_chars")
    budget_chars = int(budget) if budget is not None else None
    backends.ensure_graph_seed(scope)
    try:
        payload = backends.graph.explore(
            backends.graph_scope(scope),
            query,
            top_k=top_k,
            max_depth=max_depth,
            budget_chars=budget_chars,
        )
    except CodeGraphError as exc:
        raise ValueError(str(exc.message)) from exc
    return {**base, "graph_mode": backends.graph_mode, **payload}


def detect_changes(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    """Risk-scored review context for a set of changed files."""
    raw = arguments.get("changed_files") or arguments.get("files") or []
    if isinstance(raw, str):
        changed_files = [p.strip() for p in raw.split(",") if p.strip()]
    else:
        changed_files = [str(p).strip() for p in raw if str(p).strip()]
    if not changed_files:
        raise ValueError("changed_files is required")
    include_flows = bool(arguments.get("include_flows", True))
    backends.ensure_graph_seed(scope)
    try:
        payload = backends.graph.detect_changes(
            backends.graph_scope(scope),
            changed_files,
            include_flows=include_flows,
        )
    except CodeGraphError as exc:
        raise ValueError(str(exc.message)) from exc
    return {**base, "graph_mode": backends.graph_mode, **payload}


def architecture_overview(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    top_n = int(arguments.get("top_n") or 10)
    backends.ensure_graph_seed(scope)
    try:
        payload = backends.graph.architecture_overview(
            backends.graph_scope(scope), top_n=top_n
        )
    except CodeGraphError as exc:
        raise ValueError(str(exc.message)) from exc
    return {**base, "graph_mode": backends.graph_mode, **payload}


def symbol_path(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    start_id = str(arguments.get("start_id") or arguments.get("from") or "").strip()
    end_id = str(arguments.get("end_id") or arguments.get("to") or "").strip()
    max_depth = int(arguments.get("max_depth") or 12)
    backends.ensure_graph_seed(scope)
    try:
        payload = backends.graph.symbol_path(
            backends.graph_scope(scope),
            start_id,
            end_id,
            max_depth=max_depth,
        )
    except CodeGraphError as exc:
        raise ValueError(str(exc.message)) from exc
    return {**base, "graph_mode": backends.graph_mode, **payload}


def hybrid_search(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    query = str(arguments.get("query") or "").strip()
    if not query:
        raise ValueError("query is required")
    top_k = int(arguments.get("top_k") or 10)
    backends.ensure_graph_seed(scope)
    try:
        payload = backends.graph.hybrid_search(
            backends.graph_scope(scope), query, top_k=top_k
        )
    except CodeGraphError as exc:
        raise ValueError(str(exc.message)) from exc
    return {**base, "graph_mode": backends.graph_mode, **payload}


def freshness(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    backends.ensure_graph_seed(scope)
    file_path = str(arguments.get("file_path") or "").strip()
    if file_path:
        payload = backends.graph.mark_file_pending(file_path)
    else:
        payload = backends.graph.freshness_status()
    return {**base, "graph_mode": backends.graph_mode, **payload}


def generation_context(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    backends.ensure_graph_seed(scope)
    symbol_id = _resolve_symbol_id(backends, scope, arguments)
    max_symbols = int(arguments.get("max_symbols") or 12)
    max_symbols = max(1, min(max_symbols, 64))
    try:
        payload = backends.graph.build_generation_context(
            backends.graph_scope(scope),
            symbol_id,
            max_symbols=max_symbols,
        )
    except NotFoundError as exc:
        raise ValueError(str(exc.message)) from exc
    except CodeGraphError as exc:
        raise ValueError(str(exc.message)) from exc
    return {**base, "graph_mode": backends.graph_mode, **payload}


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


def language_profile(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    backends.ensure_graph_seed(scope)
    profile = backends.graph.get_polyglot_profile(backends.graph_scope(scope))
    payload = profile.to_dict() if hasattr(profile, "to_dict") else dict(profile)
    return {**base, "graph_mode": backends.graph_mode, "language_profile": payload}
