"""Tests for cancel-aware parallel file jobs (Ctrl+C / KeyboardInterrupt)."""

from __future__ import annotations

import threading

import pytest

import code_graph_service.application.ingest.parallel_files as mod
from code_graph_service.application.ingest.parallel_files import run_parallel_file_jobs


def test_run_parallel_file_jobs_runs_all():
    seen: list[int] = []
    lock = threading.Lock()

    def fn(index: int, item: int) -> None:
        with lock:
            seen.append(item)

    run_parallel_file_jobs(workers=3, items=[1, 2, 3, 4], fn=fn)
    assert sorted(seen) == [1, 2, 3, 4]


def test_run_parallel_file_jobs_keyboard_interrupt_cancels_pending(capsys):
    started = threading.Event()
    release = threading.Event()
    ran: list[tuple[str, int]] = []
    lock = threading.Lock()

    def fn(index: int, item: int) -> None:
        with lock:
            ran.append(("start", item))
        if item == 0:
            started.set()
        assert release.wait(timeout=5)
        with lock:
            ran.append(("done", item))

    original = mod.as_completed

    def as_completed_then_interrupt(futures, timeout=None):
        assert started.wait(timeout=5)
        release.set()
        raise KeyboardInterrupt

    mod.as_completed = as_completed_then_interrupt
    try:
        with pytest.raises(KeyboardInterrupt):
            run_parallel_file_jobs(workers=2, items=[0, 1, 2, 3], fn=fn)
    finally:
        mod.as_completed = original
        release.set()

    started_items = {entry[1] for entry in ran if entry[0] == "start"}
    done_items = {entry[1] for entry in ran if entry[0] == "done"}
    assert started_items <= {0, 1}
    assert done_items <= started_items
    assert 2 not in started_items
    assert 3 not in started_items
    assert 2 not in done_items
    assert 3 not in done_items
    out = capsys.readouterr().out
    assert "Stopping sync: cancelling" in out
    assert "workers finished" in out
