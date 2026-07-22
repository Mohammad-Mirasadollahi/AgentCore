"""Cancel-aware parallel file work for ingest/sync."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor, as_completed, wait
from typing import TypeVar

T = TypeVar("T")

# After Ctrl+C, do not block forever on hung LiteLLM/HTTP worker threads.
SHUTDOWN_GRACE_SEC = 15.0


def _shutdown_log(message: str) -> None:
    print(f"   →  {message}", flush=True)


def run_parallel_file_jobs(
    *,
    workers: int,
    items: Sequence[T],
    fn: Callable[[int, T], None],
    shutdown_grace_sec: float = SHUTDOWN_GRACE_SEC,
) -> None:
    """Run ``fn(index, item)`` over ``items``.

    On ``KeyboardInterrupt``: cancel pending futures, wait briefly for in-flight
    work, then abandon stuck workers so the CLI can exit (non-daemon pool threads
    would otherwise block process exit until LiteLLM timeouts finish).
    """
    if not items:
        return
    workers = max(1, min(int(workers), len(items)))
    if workers == 1:
        for index, item in enumerate(items):
            fn(index, item)
        return

    pool = ThreadPoolExecutor(max_workers=workers)
    futures: list[Future[None]] = []
    cancel_pending = False
    force_exit = False
    try:
        futures = [pool.submit(fn, index, item) for index, item in enumerate(items)]
        for fut in as_completed(futures):
            fut.result()
    except KeyboardInterrupt:
        cancel_pending = True
        cancelled = 0
        for fut in futures:
            if fut.cancel():
                cancelled += 1
        in_flight = sum(1 for fut in futures if fut.running())
        _shutdown_log(
            f"Stopping sync: cancelling {cancelled} queued file(s); "
            f"waiting up to {shutdown_grace_sec:g}s for {in_flight} still running"
        )
        raise
    finally:
        if cancel_pending:
            _shutdown_log("Stopping sync: finishing in-progress workers")
            grace = max(0.0, float(shutdown_grace_sec))
            running = [fut for fut in futures if not fut.done()]
            if running and grace > 0:
                wait(running, timeout=grace)
            still = [fut for fut in futures if not fut.done()]
            pool.shutdown(wait=False, cancel_futures=True)
            if still:
                force_exit = True
                _shutdown_log(
                    f"Stopping sync: abandoning {len(still)} stuck worker(s) "
                    "(likely blocked in provider HTTP)"
                )
            else:
                _shutdown_log("Stopping sync: workers finished")
        else:
            pool.shutdown(wait=True, cancel_futures=False)
        if force_exit:
            # Non-daemon ThreadPoolExecutor threads keep the interpreter alive otherwise.
            os._exit(130)
