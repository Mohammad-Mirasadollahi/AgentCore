"""Cancel-aware parallel file work for ingest/sync."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import TypeVar

T = TypeVar("T")


def _shutdown_log(message: str) -> None:
    print(f"   →  {message}", flush=True)


def run_parallel_file_jobs(
    *,
    workers: int,
    items: Sequence[T],
    fn: Callable[[int, T], None],
) -> None:
    """Run ``fn(index, item)`` over ``items``.

    On ``KeyboardInterrupt``: cancel pending futures, wait for in-flight work
    to finish (graceful stop), then re-raise so the CLI can exit cleanly.
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
            f"waiting for {in_flight} still running"
        )
        raise
    finally:
        if cancel_pending:
            _shutdown_log("Stopping sync: finishing in-progress workers")
        pool.shutdown(wait=True, cancel_futures=cancel_pending)
        if cancel_pending:
            _shutdown_log("Stopping sync: workers finished")
