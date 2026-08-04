"""Production liveness and test-only classification over the code graph."""

from __future__ import annotations

from collections import defaultdict

from ..dead_code_scoring import USE_EDGE_TYPES, is_strong_use_edge, is_weak_use_edge
from ..enums import RelType, SymbolKind
from ..flows import FlowNode, is_entry_point
from ..models import GraphEdge, GraphSymbol


def is_test_path(file_path: str) -> bool:
    path_l = (file_path or "").lower().replace("\\", "/")
    return (
        "/test" in path_l
        or path_l.startswith("tests/")
        or "/tests/" in path_l
        or path_l.endswith("_test.py")
        or path_l.startswith("test_")
        or ".spec." in path_l
        or ".test." in path_l
    )


def strong_inbound_sources(edges: list[GraphEdge]) -> dict[str, set[str]]:
    inbound: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if not is_strong_use_edge(edge):
            continue
        inbound[edge.target_id].add(edge.source_id)
    return inbound


def weak_inbound_targets(edges: list[GraphEdge]) -> set[str]:
    return {edge.target_id for edge in edges if is_weak_use_edge(edge)}


def any_inbound_counts(edges: list[GraphEdge]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for edge in edges:
        if edge.rel_type not in USE_EDGE_TYPES:
            continue
        counts[edge.target_id] += 1
    return counts


def live_ids_in_pool(
    pool_ids: set[str],
    by_id: dict[str, GraphSymbol],
    edges: list[GraphEdge],
    *,
    all_ids: set[str],
) -> set[str]:
    """Reachability from production live roots (outside pool ∪ non-test entrypoints).

    Strong edges that originate in test paths do not propagate production liveness
    (Necro ``test_only`` verdict). Those symbols remain candidates with ``test_only``.
    """
    strong_sources = strong_inbound_sources(edges)
    outbound: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if not is_strong_use_edge(edge):
            continue
        src_sym = by_id.get(edge.source_id)
        if src_sym is not None and is_test_path(src_sym.file_path):
            continue
        outbound[edge.source_id].add(edge.target_id)

    outside = all_ids - pool_ids
    live: set[str] = set()
    for sid in pool_ids:
        symbol = by_id.get(sid)
        if symbol is None:
            continue
        if is_test_path(symbol.file_path):
            continue
        sources = strong_sources.get(sid, set())
        prod_outside = {
            src
            for src in sources & outside
            if (src_sym := by_id.get(src)) is not None and not is_test_path(src_sym.file_path)
        }
        if prod_outside:
            live.add(sid)
            continue
        any_in = len(sources)
        node = FlowNode(
            id=symbol.id,
            name=symbol.name,
            qualified_name=symbol.qualified_name,
            file_path=symbol.file_path,
            signature=symbol.signature,
            body=symbol.body,
        )
        if is_entry_point(node, inbound_call_count=any_in, is_route_handler=False):
            live.add(sid)

    stack = list(live)
    while stack:
        src = stack.pop()
        for tgt in outbound.get(src, ()):
            if tgt in pool_ids and tgt not in live:
                live.add(tgt)
                stack.append(tgt)
    return live


def file_has_live_importers(
    file_path: str,
    symbols: list[GraphSymbol],
    edges: list[GraphEdge],
    live_ids: set[str],
) -> bool:
    path = (file_path or "").replace("\\", "/")
    ids_in_file = {
        s.id for s in symbols if (s.file_path or "").replace("\\", "/") == path
    }
    for edge in edges:
        if edge.rel_type != RelType.IMPORTS.value:
            continue
        if edge.target_id in ids_in_file and edge.source_id in live_ids:
            return True
        tgt = next((s for s in symbols if s.id == edge.target_id), None)
        if tgt and tgt.kind == SymbolKind.FILE and (tgt.file_path or "").replace("\\", "/") == path:
            if edge.source_id in live_ids or edge.source_id not in ids_in_file:
                return True
    return False


def test_only_for_symbol(
    sid: str,
    by_id: dict[str, GraphSymbol],
    strong_sources: dict[str, set[str]],
    edges: list[GraphEdge] | None = None,
) -> bool:
    """True when the only strong references are from test paths, or TESTED_BY-only."""
    sources = strong_sources.get(sid, set())
    prod_sources = [
        src
        for src in sources
        if (sym := by_id.get(src)) is not None and not is_test_path(sym.file_path)
    ]
    if prod_sources:
        return False
    if sources:
        return True
    if not edges:
        return False
    for edge in edges:
        if edge.rel_type != RelType.TESTED_BY.value:
            continue
        if edge.source_id != sid:
            continue
        tgt = by_id.get(edge.target_id)
        if tgt is not None and is_test_path(tgt.file_path):
            return True
    return False
