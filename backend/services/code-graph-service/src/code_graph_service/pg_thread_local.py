"""Per-thread ``psycopg`` connections for parallel store writers.

Role: own one connection per worker thread so concurrent ingest does not share
cursors. Source of truth: the caller’s connect factory; tracked set for close.
Allowed: lazy connect on first use per thread; close-all on shutdown; drop/retry
after server-side disconnect (Postgres restart / AdminShutdown).
Forbidden: returning a closed connection; sharing one connection across threads.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

_TRANSIENT_MARKERS = (
    "adminshutdown",
    "connectiondoesnotexist",
    "defunct connection",
    "server closed the connection",
    "connection not open",
    "ssl connection has been closed",
    "terminating connection due to administrator command",
    "connection refused",
    "could not connect to server",
)


def is_transient_db_error(exc: BaseException) -> bool:
    """True for dead/restarted Postgres (or similar) transport failures worth one retry."""
    name = type(exc).__name__
    blob = f"{name}:{exc}".lower()
    if name in {"AdminShutdown", "InterfaceError", "ServiceUnavailable"}:
        return True
    if name in {"OperationalError", "DatabaseError"} and any(m in blob for m in _TRANSIENT_MARKERS):
        return True
    return any(m in blob for m in _TRANSIENT_MARKERS)


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
        if conn is not None:
            self._local.connection = None
        conn = self._connect()
        self._local.connection = conn
        with self._lock:
            self._all.append(conn)
        return conn

    def drop(self) -> None:
        """Forget the current thread’s connection after a transport error."""
        conn = getattr(self._local, "connection", None)
        self._local.connection = None
        if conn is None:
            return
        with self._lock:
            try:
                self._all.remove(conn)
            except ValueError:
                pass
        try:
            if not conn.closed:
                conn.close()
        except Exception:  # noqa: BLE001 — best-effort
            pass

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
