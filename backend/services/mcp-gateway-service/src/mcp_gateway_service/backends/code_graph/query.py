"""MCP read/query handlers for the code-knowledge graph."""

from __future__ import annotations

from typing import Any

from code_graph_service.domain.errors import CodeGraphError, NotFoundError

from ..platform import PlatformBackends
from ._resolve import resolve_symbol_id

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
    symbol_id = resolve_symbol_id(backends, scope, arguments)
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
    symbol_id = resolve_symbol_id(backends, scope, arguments)
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
    symbol_id = resolve_symbol_id(backends, scope, arguments)
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
    symbol_id = resolve_symbol_id(backends, scope, arguments)
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

