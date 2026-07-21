"""Tests for sync progress tracker and ETA formatting."""

from __future__ import annotations

import json
import time
from pathlib import Path

from agentcore_cli.sync_progress import (
    SyncProgressTracker,
    format_bar,
    format_duration,
    read_live_progress,
)


def test_format_duration_and_bar():
    assert format_duration(5) == "5s"
    assert format_duration(65) == "1m 5s"
    assert format_bar(50, width=10) == "[#####-----]"


def test_tracker_writes_progress_and_adapts(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr("agentcore_cli.ui._use_color", lambda: False)
    progress_file = tmp_path / "sync-progress.json"
    tracker = SyncProgressTracker(
        scope="mir/dev/app",
        path=str(tmp_path),
        interval_sec=0.01,
        progress_file=progress_file,
    )
    total = 10
    for i in range(total + 1):
        tracker(
            {
                "phase": "ingest",
                "done": i,
                "total": total,
                "file": f"f{i}.py",
                "status": "started" if i == 0 else ("finished" if i == total else "ok"),
                "symbols_indexed": i * 2,
                "edges_written": i,
                "chars_read": i * 40,
                "approx_tokens": i * 10,
            }
        )
        time.sleep(0.02)
        if i == 5:
            assert progress_file.is_file()
            data = json.loads(progress_file.read_text(encoding="utf-8"))
            assert data["done"] == 5
            assert data["total"] == 10
    tracker.finish()
    assert not progress_file.is_file()
    out = capsys.readouterr().out
    assert "%" in out
    assert "files" in out


def test_read_live_progress_fresh(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("agentcore_cli.sync_progress.repo_root", lambda: tmp_path)
    path = tmp_path / ".agentcore" / "sync-progress.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "active": True,
                "percent": 40,
                "done": 4,
                "total": 10,
                "elapsed_sec": 20,
                "eta_sec": 30,
                "pid": __import__("os").getpid(),
                "updated_at": time.time(),
            }
        ),
        encoding="utf-8",
    )
    data = read_live_progress(root=tmp_path)
    assert data is not None
    assert data["percent"] == 40


def test_ingest_calls_on_progress(tmp_path: Path):
    from code_graph_service.core import CodeGraphService, Scope
    from code_graph_service.testing import InMemoryStore

    root = tmp_path / "src"
    root.mkdir()
    (root / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
    (root / "b.py").write_text("def b():\n    return 2\n", encoding="utf-8")
    events: list[dict] = []
    svc = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "p")
    svc.ingest_repo(
        scope,
        "cli",
        "c1",
        "k1",
        {
            "root_path": str(root),
            "max_files": 10,
            "include_outcomes": False,
            "on_progress": events.append,
        },
    )
    assert events
    assert events[0]["status"] == "started"
    assert events[-1]["status"] == "finished"
    assert events[-1]["total"] >= 2
    assert events[-1]["done"] == events[-1]["total"]
