"""Per-thread ``psycopg`` connections for parallel store writers.

Role: own one connection per worker thread so concurrent ingest does not share
cursors. Source of truth: the caller’s connect factory; tracked set for close.
Allowed: lazy connect on first use per thread; close-all on shutdown.
Forbidden: returning a closed connection; sharing one connection across threads.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any


class ThreadLocalPsycopg:
    """Lazy per-thread ``psycopg`` connection registry."""

    def __init__(self, connect: Callable[[], Any]) -> None:
        self._connect = connect
        self._local = threading.local()
        self._all: list[Any] = []
        self._lock = threading.Lock()

    def get(self) -> Any:
        conn = getattr(self._local, "connection", None)
        if conn is not None and not conn.closed:
            return conn
        conn = self._connect()
        self._local.connection = conn
        with self._lock:
            self._all.append(conn)
        return conn

    def close_all(self) -> None:
        with self._lock:
            conns = list(self._all)
            self._all.clear()
        for conn in conns:
            try:
                if not conn.closed:
                    conn.close()
            except Exception:  # noqa: BLE001 — best-effort shutdown
                pass
        self._local.connection = None
