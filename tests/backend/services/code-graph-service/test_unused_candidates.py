"""Unit tests for unused-symbol candidate detection."""

from __future__ import annotations

from code_graph_service.domain.enums import CallConfidence, DocStatus, RelType, SymbolKind
from code_graph_service.domain.models import GraphEdge, GraphSymbol, Scope
from code_graph_service.domain.unused_candidates import find_unused_candidates

SCOPE = Scope("t", "w", "p")


def _sym(
    sid: str,
    name: str,
    *,
    kind: SymbolKind = SymbolKind.FUNCTION,
    path: str = "pkg/mod.py",
    body: str = "return 1",
) -> GraphSymbol:
    return GraphSymbol(
        id=sid,
        scope=SCOPE,
        kind=kind,
        file_path=path,
        name=name,
        qualified_name=f"pkg.mod.{name}",
        signature=f"def {name}():",
        body=body,
        hash_value="h",
        ai_documentation="",
        doc_status=DocStatus.UNCHANGED,
        embedding=[],
    )


def test_changed_symbols_unused_helper():
    helper = _sym("s:helper", "old_helper")
    caller = _sym("s:caller", "run")
    edges = [
        GraphEdge(
            id="e1",
            scope=SCOPE,
            rel_type=RelType.CALLS.value,
            source_id=caller.id,
            target_id="s:other",
            confidence=CallConfidence.EXACT,
        )
    ]
    # helper has no inbound CALLS/IMPORTS
    out = find_unused_candidates(
        [helper, caller],
        edges,
        scope_mode="changed_symbols",
        anchor_symbols=["old_helper"],
    )
    assert out["freshness"] == "ok"
    assert len(out["candidates"]) == 1
    assert out["candidates"][0]["safe_to_delete"] is True
    assert out["candidates"][0]["symbol"].endswith("old_helper")


def test_entrypoint_goes_to_uncertain():
    main = _sym("s:main", "main", body="print('hi')")
    out = find_unused_candidates(
        [main],
        [],
        scope_mode="explicit_paths",
        anchor_paths=["pkg/mod.py"],
        include_uncertain=True,
    )
    assert out["candidates"] == []
    assert out["skipped_uncertain"]
    assert "entrypoint" in out["skipped_uncertain"][0]["blockers"]


def test_no_anchors_refuses_repo_scan():
    helper = _sym("s:helper", "orphan")
    out = find_unused_candidates([helper], [], scope_mode="changed_symbols")
    assert out["candidates"] == []
    assert out.get("note") == "no_anchor_symbols_or_paths"


def test_inbound_call_excludes_symbol():
    helper = _sym("s:helper", "helper")
    caller = _sym("s:caller", "run")
    edges = [
        GraphEdge(
            id="e1",
            scope=SCOPE,
            rel_type=RelType.CALLS.value,
            source_id=caller.id,
            target_id=helper.id,
            confidence=CallConfidence.EXACT,
        )
    ]
    out = find_unused_candidates(
        [helper, caller],
        edges,
        scope_mode="changed_symbols",
        anchor_symbols=["helper"],
    )
    assert out["candidates"] == []
