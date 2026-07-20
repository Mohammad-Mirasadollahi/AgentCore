"""Store wrapper that mirrors outbox events to PostgreSQL for the relay worker."""

from __future__ import annotations

from typing import Any

from .domain.ports import Store
from .postgres_side import PostgresOutboxMirror


class OutboxMirrorStore:
    """Delegates the Store port and dual-writes append_event to Postgres outbox."""

    def __init__(self, store: Store, mirror: PostgresOutboxMirror) -> None:
        self._store = store
        self._mirror = mirror

    @property
    def inner(self) -> Store:
        return self._store

    def close(self) -> None:
        close = getattr(self._store, "close", None)
        if callable(close):
            close()
        self._mirror.close()

    def append_event(self, event: dict[str, Any]) -> None:
        self._store.append_event(event)
        self._mirror.append_event(event)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._store, name)
