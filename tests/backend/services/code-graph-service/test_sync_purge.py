"""Tests for auto sync_repo policy and purge_scope."""

from __future__ import annotations

from pathlib import Path

from code_graph_service.core import CodeGraphService, Scope
from code_graph_service.testing import InMemoryStore


def _write_tree(root: Path, *, count: int = 2) -> None:
    src = root / "src"
    src.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (src / f"f{i}.py").write_text(f"def f{i}():\n    return {i}\n", encoding="utf-8")


def test_sync_empty_graph_is_full(tmp_path: Path):
    _write_tree(tmp_path)
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "p")
    result = service.sync_repo(
        scope,
        "tester",
        "corr-sync-1",
        "sync-key-1",
        {"root_path": str(tmp_path), "include_outcomes": True},
    )
    assert result.mode == "full"
    assert result.files_ingested == 2
    assert len(service.store.list_symbols(scope)) >= 2


def test_sync_with_pending_is_incremental(tmp_path: Path):
    _write_tree(tmp_path, count=2)
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "p")
    service.sync_repo(
        scope,
        "tester",
        "corr-sync-seed",
        "sync-seed",
        {"root_path": str(tmp_path), "max_files": 1, "include_outcomes": True},
    )
    service.mark_file_pending("src/f1.py")
    result = service.sync_repo(
        scope,
        "tester",
        "corr-sync-2",
        "sync-key-2",
        {"root_path": str(tmp_path), "include_outcomes": True},
    )
    assert result.mode == "incremental"
    assert result.files_discovered == 1
    assert result.files_ingested == 1


def test_sync_with_symbols_no_pending_is_incremental_walk(tmp_path: Path):
    _write_tree(tmp_path)
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "p")
    service.sync_repo(
        scope,
        "tester",
        "corr-a",
        "key-a",
        {"root_path": str(tmp_path), "include_outcomes": True},
    )
    result = service.sync_repo(
        scope,
        "tester",
        "corr-b",
        "key-b",
        {"root_path": str(tmp_path), "include_outcomes": True},
    )
    assert result.mode == "incremental"
    assert result.files_discovered == 2


def test_sync_truncated_hint_and_continue(tmp_path: Path):
    _write_tree(tmp_path, count=4)
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "p-trunc")
    first = service.sync_repo(
        scope,
        "tester",
        "corr-t1",
        "key-t1",
        {"root_path": str(tmp_path), "max_files": 2, "include_outcomes": True},
    )
    assert first.mode == "full"
    assert first.truncated is True
    assert "run sync again" in first.hint
    second = service.sync_repo(
        scope,
        "tester",
        "corr-t2",
        "key-t2",
        {"root_path": str(tmp_path), "max_files": 2, "include_outcomes": True},
    )
    assert second.mode == "incremental"
    assert second.files_ingested >= 1


def test_purge_wipes_scope(tmp_path: Path):
    _write_tree(tmp_path)
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "p-purge")
    service.sync_repo(
        scope,
        "tester",
        "corr-p",
        "key-p",
        {"root_path": str(tmp_path), "include_outcomes": True},
    )
    assert service.store.list_symbols(scope)
    service.mark_file_pending("src/f0.py")
    wiped = service.purge_scope(scope)
    assert wiped["ok"] is True
    assert wiped["symbols_after"] == 0
    assert wiped["edges_after"] == 0
    assert service.freshness_status()["pending_count"] == 0
    again = service.sync_repo(
        scope,
        "tester",
        "corr-p2",
        "key-p2",
        {"root_path": str(tmp_path), "include_outcomes": True},
    )
    assert again.mode == "full"
