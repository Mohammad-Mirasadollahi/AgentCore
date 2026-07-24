"""Graph-backed unused-symbol candidates (dead-code cleanup loop).

AgentCore never mutates the repository — this module only surfaces candidates.
Normative contract: docs/07-code-knowledge-graph/36-dead-code-candidates-and-cleanup-loop.md
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable

from .enums import RelType, SymbolKind
from .flows import FlowNode, is_entry_point
from .models import GraphEdge, GraphSymbol

_USE_EDGE_TYPES = frozenset({RelType.CALLS.value, RelType.IMPORTS.value})

_SCOPE_MODES = frozenset({"task_neighborhood", "changed_symbols", "explicit_paths"})

_TSOC_DEFER = re.compile(r"tsoc-defer\s*:", re.IGNORECASE)
_STRING_REGISTRY_HINT = re.compile(
    r"(PERMISSION|ROUTE|FEATURE_FLAG|REGISTRY|HANDLERS)\s*=\s*[{\[]",
    re.IGNORECASE,
)
_PUBLIC_HTTP_HINT = re.compile(
    r"@(?:app|router|blueprint)\.(?:get|post|put|delete|patch|route)\b|"
    r"APIRouter\(|FastAPI\(|@require_permission\b",
    re.IGNORECASE,
)


def _inbound_use_counts(edges: Iterable[GraphEdge]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for edge in edges:
        if edge.rel_type not in _USE_EDGE_TYPES:
            continue
        counts[edge.target_id] += 1
    return counts


def _neighbor_ids(
    edges: Iterable[GraphEdge],
    seeds: set[str],
    *,
    max_hops: int = 1,
) -> set[str]:
    if not seeds:
        return set()
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        adjacency[edge.source_id].add(edge.target_id)
        adjacency[edge.target_id].add(edge.source_id)
    frontier = set(seeds)
    seen = set(seeds)
    for _ in range(max(1, max_hops)):
        nxt: set[str] = set()
        for node in frontier:
            for other in adjacency.get(node, ()):
                if other not in seen:
                    seen.add(other)
                    nxt.add(other)
        frontier = nxt
        if not frontier:
            break
    return seen


def _resolve_anchors(
    symbols: list[GraphSymbol],
    *,
    anchor_symbols: list[str] | None,
    anchor_paths: list[str] | None,
) -> set[str]:
    wanted_names = {s.strip() for s in (anchor_symbols or []) if str(s).strip()}
    wanted_paths = {p.strip().replace("\\", "/") for p in (anchor_paths or []) if str(p).strip()}
    if not wanted_names and not wanted_paths:
        return set()
    ids: set[str] = set()
    for sym in symbols:
        qn = sym.qualified_name or ""
        path = (sym.file_path or "").replace("\\", "/")
        if sym.id in wanted_names or qn in wanted_names or sym.name in wanted_names:
            ids.add(sym.id)
            continue
        if any(path == wp or path.startswith(wp.rstrip("/") + "/") or path.endswith("/" + wp) for wp in wanted_paths):
            ids.add(sym.id)
            continue
        if any(wp and wp in path for wp in wanted_paths):
            ids.add(sym.id)
    return ids


def _blockers_for(symbol: GraphSymbol, *, inbound: int) -> list[str]:
    blockers: list[str] = []
    blob = f"{symbol.signature}\n{symbol.body[:800]}"
    node = FlowNode(
        id=symbol.id,
        name=symbol.name,
        qualified_name=symbol.qualified_name,
        file_path=symbol.file_path,
        signature=symbol.signature,
        body=symbol.body,
    )
    if is_entry_point(node, inbound_call_count=inbound, is_route_handler=False):
        blockers.append("entrypoint")
    if _PUBLIC_HTTP_HINT.search(blob):
        blockers.append("public_http_handler")
    if _STRING_REGISTRY_HINT.search(blob) or "__getattr__" in blob:
        blockers.append("possible_string_registry")
    if _TSOC_DEFER.search(blob):
        blockers.append("tsoc_defer")
    if symbol.kind == SymbolKind.EXTERNAL:
        blockers.append("external_symbol")
    if symbol.visibility == "public" and symbol.kind in {
        SymbolKind.FUNCTION,
        SymbolKind.METHOD,
        SymbolKind.CLASS,
    }:
        # Soft signal — listed as blocker only when already uncertain
        pass
    path_l = (symbol.file_path or "").lower()
    if "/test" in path_l or path_l.startswith("tests/") or "/tests/" in path_l:
        blockers.append("tests_only_path")
    return blockers


def find_unused_candidates(
    symbols: list[GraphSymbol],
    edges: list[GraphEdge],
    *,
    scope_mode: str,
    anchor_symbols: list[str] | None = None,
    anchor_paths: list[str] | None = None,
    max_results: int = 50,
    include_uncertain: bool = False,
    freshness: str = "ok",
) -> dict[str, Any]:
    """Return unused-candidate payload for MCP / service callers."""
    mode = (scope_mode or "").strip()
    if mode not in _SCOPE_MODES:
        raise ValueError(
            "scope_mode must be one of: task_neighborhood, changed_symbols, explicit_paths"
        )
    max_results = max(1, min(int(max_results or 50), 200))

    by_id = {s.id: s for s in symbols}
    inbound = _inbound_use_counts(edges)
    anchors = _resolve_anchors(symbols, anchor_symbols=anchor_symbols, anchor_paths=anchor_paths)

    if mode == "explicit_paths":
        pool_ids = anchors if anchors else set()
    elif mode == "changed_symbols":
        pool_ids = anchors if anchors else set()
    else:  # task_neighborhood
        pool_ids = _neighbor_ids(edges, anchors, max_hops=1) if anchors else set()

    # Without anchors, refuse whole-repo scan (programming profile default).
    if not pool_ids:
        return {
            "freshness": freshness,
            "scope_mode": mode,
            "candidates": [],
            "skipped_uncertain": [],
            "note": "no_anchor_symbols_or_paths",
        }

    eligible_kinds = {
        SymbolKind.FUNCTION,
        SymbolKind.METHOD,
        SymbolKind.CLASS,
    }
    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for sid in sorted(pool_ids):
        symbol = by_id.get(sid)
        if symbol is None:
            continue
        if symbol.kind not in eligible_kinds:
            continue
        if symbol.kind == SymbolKind.FILE:
            continue
        in_count = inbound.get(sid, 0)
        if in_count > 0:
            continue

        reasons = ["no_inbound_calls", "no_inbound_imports"]
        blockers = _blockers_for(symbol, inbound=in_count)
        confidence = "high"
        if freshness in {"stale", "pending_sync"}:
            confidence = "medium"
            blockers = list(dict.fromkeys([*blockers, f"freshness_{freshness}"]))
        if blockers:
            confidence = "low"

        row = {
            "symbol": symbol.qualified_name or symbol.name,
            "symbol_id": symbol.id,
            "path": symbol.file_path,
            "kind": symbol.kind.value if hasattr(symbol.kind, "value") else str(symbol.kind),
            "confidence": confidence,
            "reasons": reasons,
            "blockers": blockers,
            "safe_to_delete": confidence == "high" and not blockers,
        }
        if row["safe_to_delete"]:
            candidates.append(row)
        elif include_uncertain or blockers:
            skipped.append(
                {
                    "symbol": row["symbol"],
                    "symbol_id": row["symbol_id"],
                    "path": row["path"],
                    "confidence": row["confidence"],
                    "blockers": row["blockers"],
                }
            )

    return {
        "freshness": freshness,
        "scope_mode": mode,
        "candidates": candidates[:max_results],
        "skipped_uncertain": skipped[:max_results],
    }
