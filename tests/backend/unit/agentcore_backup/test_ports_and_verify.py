"""Unit tests for store ports, neo4j gates, and post-restore verification."""

from __future__ import annotations

import pytest

from agentcore_backup.neo4j_store import (
    graph_store_expects_neo4j,
    require_neo4j_for_export,
)
from agentcore_backup.orchestrator import _verify_imported_counts
from agentcore_backup.ports import build_ports
from agentcore_backup.tables import STORE_ORDER


def test_ports_cover_all_non_local_stores():
    ports = {p.store_id for p in build_ports()}
    expected = {s for s in STORE_ORDER if s != "local"}
    assert ports == expected
    assert "memory" in ports
    assert "audit" in ports
    assert "reporting" in ports


def test_verify_imported_counts_fail_closed():
    with pytest.raises(RuntimeError, match="count verification failed"):
        _verify_imported_counts(
            manifest_stores={"memory": {"row_count": 5}},
            imported={"memory": 2},
        )
    ok = _verify_imported_counts(
        manifest_stores={"memory": {"row_count": 5}},
        imported={"memory": 5},
    )
    assert ok["ok"] is True


def test_require_neo4j_when_store_is_neo4j(monkeypatch):
    monkeypatch.setenv("AGENTCORE_CODE_GRAPH_STORE", "neo4j")
    monkeypatch.delenv("AGENTCORE_NEO4J_PASSWORD", raising=False)
    assert graph_store_expects_neo4j() is True
    with pytest.raises(RuntimeError, match="refuse export"):
        require_neo4j_for_export()
