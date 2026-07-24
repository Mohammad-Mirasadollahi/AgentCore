"""Unit tests for thread-safe docs-sync store adapters."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

from docs_sync_service.core import Document, DocumentState, Scope
from docs_sync_service.postgres_store import PostgresStore
from docs_sync_service.testing import InMemoryStore

SCOPE = Scope("t", "w", "p")


def _doc(doc_id: str) -> Document:
    return Document(
        doc_id,
        SCOPE,
        "actor",
        "corr",
        f"docs/{doc_id}.md",
        doc_id,
        "platform",
        DocumentState.INDEXED,
        "1.0.0",
        [],
        [],
        {"doc_id": doc_id},
        "body",
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:00:00Z",
        1,
    )


def test_inmemory_store_put_document_is_safe_under_threads():
    store = InMemoryStore()
    errors: list[BaseException] = []

    def _write(i: int) -> None:
        try:
            store.put_document(_doc(f"d{i}"))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(_write, range(40)))
    assert errors == []
    assert len(store.list_documents(SCOPE)) == 40


def test_postgres_store_uses_per_thread_connections():
    created: list[object] = []
    lock = threading.Lock()
    errors: list[BaseException] = []

    class _Conn:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

        def cursor(self):
            raise AssertionError("cursor not used in this unit test")

    def fake_connect(*_args, **_kwargs):
        conn = _Conn()
        with lock:
            created.append(conn)
        return conn

    fake_psycopg = MagicMock()
    fake_psycopg.connect.side_effect = fake_connect
    store = PostgresStore.__new__(PostgresStore)
    store._psycopg = fake_psycopg
    store._row_factory = object()
    store._json = object()
    store._database_url = "postgresql://localhost/docs"
    store._local = threading.local()
    store._all_connections = []
    store._all_lock = threading.Lock()

    seen: dict[int, int] = {}
    barrier = threading.Barrier(4)

    def worker() -> None:
        try:
            barrier.wait(timeout=5)
            a = store._connection
            b = store._connection
            assert a is b
            seen[threading.get_ident()] = id(a)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert len(seen) == 4
    assert len(set(seen.values())) == 4
    assert len(created) == 4
    store.close()
    assert all(c.closed for c in created)
