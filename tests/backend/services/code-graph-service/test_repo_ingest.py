"""Tests for repository discovery and bulk ingest."""

from __future__ import annotations

import threading
from pathlib import Path

from code_graph_service.core import CodeGraphService, Scope
from code_graph_service.domain.repo_discovery import discover_source_files
from code_graph_service.locked_store import LockedStore
from code_graph_service.testing import InMemoryStore


def _write_tree(root: Path) -> None:
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    (root / "src" / "b.py").write_text(
        "from a import alpha\n\ndef beta():\n    return alpha()\n",
        encoding="utf-8",
    )
    (root / "node_modules" / "pkg").mkdir(parents=True)
    (root / "node_modules" / "pkg" / "ignored.py").write_text("def no():\n    pass\n", encoding="utf-8")
    (root / "readme.md").write_text("# hi\n", encoding="utf-8")


def test_discover_source_files_skips_excluded_and_unknown(tmp_path: Path):
    _write_tree(tmp_path)
    found = discover_source_files(tmp_path, exclude_dirs=["node_modules"])
    paths = {item.relative_path for item in found}
    assert paths == {"src/a.py", "src/b.py"}
    assert all(item.language == "python" for item in found)


def test_discover_respects_max_files(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    for i in reversed(range(5)):
        (src / f"f{i}.py").write_text(f"def f{i}():\n    return {i}\n", encoding="utf-8")
    found = discover_source_files(tmp_path, max_files=2)
    assert [item.relative_path for item in found] == ["src/f0.py", "src/f1.py"]


def test_ingest_repo_indexes_tree(tmp_path: Path):
    _write_tree(tmp_path)
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "p")
    result = service.ingest_repo(
        scope,
        "tester",
        "corr-1",
        "repo-key-1",
        {"root_path": str(tmp_path), "include_outcomes": True, "exclude_dirs": ["node_modules"]},
    )
    assert result.files_discovered == 2
    assert result.files_ingested == 2
    assert result.files_failed == 0
    assert result.symbols_indexed >= 2
    assert not result.truncated
    symbols = service.store.list_symbols(scope)
    names = {s.name for s in symbols}
    assert "alpha" in names
    assert "beta" in names


def test_ingest_repo_reports_truncation(tmp_path: Path):
    src = tmp_path / "pkg"
    src.mkdir()
    for i in range(4):
        (src / f"m{i}.py").write_text(f"def m{i}():\n    return {i}\n", encoding="utf-8")
    service = CodeGraphService(InMemoryStore())
    result = service.ingest_repo(
        Scope("t", "w", "p2"),
        "tester",
        "corr-2",
        "repo-key-2",
        {"root_path": str(tmp_path), "max_files": 2, "include_outcomes": False},
    )
    assert result.files_discovered == 2
    assert result.truncated is True
    assert result.outcomes == []


def test_capped_repo_sync_prioritizes_changed_known_files(tmp_path: Path):
    src = tmp_path / "pkg"
    src.mkdir()
    for i in range(4):
        (src / f"m{i}.py").write_text(f"def f{i}():\n    return {i}\n", encoding="utf-8")
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "capped-known")

    for run in range(2):
        service.ingest_repo(
            scope,
            "tester",
            f"corr-{run}",
            f"repo-key-{run}",
            {"root_path": str(tmp_path), "max_files": 2},
        )

    changed_path = src / "m3.py"
    changed_path.write_text("def f3():\n    return 99\n", encoding="utf-8")
    result = service.ingest_repo(
        scope,
        "tester",
        "corr-changed",
        "repo-key-changed",
        {"root_path": str(tmp_path), "max_files": 2},
    )

    changed_file = service.store.get_symbol("file:capped-known:pkg/m3.py", scope)
    assert "return 99" in changed_file.body
    assert result.files_ingested >= 1


def test_capped_repo_sync_continues_beyond_probe_horizon(tmp_path: Path):
    src = tmp_path / "pkg"
    src.mkdir()
    for i in range(45):
        (src / f"m{i:02}.py").write_text(
            f"def f{i}():\n    return {i}\n",
            encoding="utf-8",
        )
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "probe-horizon")

    for run in range(20):
        service.ingest_repo(
            scope,
            "tester",
            f"corr-{run}",
            f"repo-key-{run}",
            {"root_path": str(tmp_path), "max_files": 2},
        )
    result = service.ingest_repo(
        scope,
        "tester",
        "corr-after-horizon",
        "repo-key-after-horizon",
        {"root_path": str(tmp_path), "max_files": 2},
    )

    files = [symbol for symbol in service.store.list_symbols(scope) if symbol.kind.value == "file"]
    assert len(files) == 42
    assert result.truncated is True


def test_api_exposes_ingest_repo_route():
    from code_graph_service.api import app

    routes = {route.path for route in app(CodeGraphService(InMemoryStore())).routes}
    assert "/api/v1/projects/{project_id}/graph/ingest-repo" in routes


def test_parallel_repo_relinks_cross_file_imports(monkeypatch, tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("class Base:\n    pass\n", encoding="utf-8")
    (src / "b.py").write_text(
        "from a import Base\n\nclass Child(Base):\n    pass\n",
        encoding="utf-8",
    )
    consumer_started = threading.Event()

    class OrderedDocs:
        def generate(self, symbol, _neighbors):
            if symbol.file_path.endswith("a.py"):
                assert consumer_started.wait(timeout=2.0)
            else:
                consumer_started.set()
            return "doc"

    monkeypatch.setenv("AGENTCORE_SYNC_MAX_FILE_WORKERS", "2")
    service = CodeGraphService(LockedStore(InMemoryStore()), docs=OrderedDocs())
    scope = Scope("t", "w", "parallel-imports")

    result = service.ingest_repo(
        scope,
        "tester",
        "corr-parallel",
        "repo-parallel",
        {"root_path": str(tmp_path), "include_outcomes": True},
    )

    assert result.files_failed == 0
    imports = [
        edge
        for edge in service.store.list_edges(scope)
        if edge.rel_type == "IMPORTS" and edge.metadata.get("file_path") == "src/b.py"
    ]
    assert any(edge.target_id == "file:parallel-imports:src/a.py" for edge in imports)
    assert not any(edge.target_id.startswith("ext:") for edge in imports)
    inherits = [
        edge
        for edge in service.store.list_edges(scope)
        if edge.rel_type == "INHERITS_FROM" and edge.metadata.get("file_path") == "src/b.py"
    ]
    assert any(edge.target_id == "sym:parallel-imports:src.a.Base" for edge in inherits)
    assert not any(edge.target_id.startswith("unresolved:") for edge in inherits)


def test_ingest_repo_progress_reports_prior_vs_queue(tmp_path: Path):
    _write_tree(tmp_path)
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "prior-queue")
    service.ingest_repo(
        scope,
        "tester",
        "corr-a",
        "repo-a",
        {"root_path": str(tmp_path), "exclude_dirs": ["node_modules"]},
    )
    events: list[dict] = []
    service.ingest_repo(
        scope,
        "tester",
        "corr-b",
        "repo-b",
        {
            "root_path": str(tmp_path),
            "exclude_dirs": ["node_modules"],
            "on_progress": events.append,
        },
    )
    started = next(e for e in events if e.get("status") == "started")
    assert started["prior_indexed"] == 2
    assert started["queue_new"] == 0
    assert started["queue_changed"] == 0
    assert started["queue_unchanged"] == 2
    assert started["done"] == 0
    # Recheck-only: denominator falls back to all selected files.
    assert started["total"] == 2


def test_ingest_repo_progress_total_excludes_unchanged_recheck(tmp_path: Path):
    """Progress done/total is new+changed only; inventory totals stay in preflight stats."""
    _write_tree(tmp_path)
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "progress-need")
    service.ingest_repo(
        scope,
        "tester",
        "corr-a",
        "repo-a",
        {"root_path": str(tmp_path), "exclude_dirs": ["node_modules"]},
    )
    (tmp_path / "src" / "a.py").write_text(
        "def alpha():\n    return 99\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "c.py").write_text("def gamma():\n    return 3\n", encoding="utf-8")
    events: list[dict] = []
    service.ingest_repo(
        scope,
        "tester",
        "corr-b",
        "repo-b",
        {
            "root_path": str(tmp_path),
            "exclude_dirs": ["node_modules"],
            "on_progress": events.append,
        },
    )
    started = next(e for e in events if e.get("status") == "started")
    assert started["prior_indexed"] == 2
    assert started["queue_new"] == 1
    assert started["queue_changed"] == 1
    assert started["queue_unchanged"] == 1
    assert started["total"] == 2  # not 3 (unchanged recheck excluded)
    finished = next(e for e in events if e.get("status") == "finished")
    assert finished["done"] == finished["total"] == 2
