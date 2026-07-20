"""Tests for repository discovery and bulk ingest."""

from __future__ import annotations

from pathlib import Path

from code_graph_service.core import CodeGraphService, Scope
from code_graph_service.domain.repo_discovery import discover_source_files
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
    found = discover_source_files(tmp_path)
    paths = {item.relative_path for item in found}
    assert paths == {"src/a.py", "src/b.py"}
    assert all(item.language == "python" for item in found)


def test_discover_respects_max_files(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(5):
        (src / f"f{i}.py").write_text(f"def f{i}():\n    return {i}\n", encoding="utf-8")
    found = discover_source_files(tmp_path, max_files=2)
    assert len(found) == 2


def test_ingest_repo_indexes_tree(tmp_path: Path):
    _write_tree(tmp_path)
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "p")
    result = service.ingest_repo(
        scope,
        "tester",
        "corr-1",
        "repo-key-1",
        {"root_path": str(tmp_path), "include_outcomes": True},
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


def test_api_exposes_ingest_repo_route():
    from code_graph_service.api import app

    routes = {route.path for route in app(CodeGraphService(InMemoryStore())).routes}
    assert "/api/v1/projects/{project_id}/graph/ingest-repo" in routes
