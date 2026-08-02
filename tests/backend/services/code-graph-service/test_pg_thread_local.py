"""Unit tests for per-thread Postgres connections."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from code_graph_service.pg_thread_local import ThreadLocalPsycopg
from code_graph_service.testing import InMemoryStore
from code_graph_service.core import Scope
from code_graph_service.domain.models import GraphSymbol
from code_graph_service.domain.enums import DocStatus, SymbolKind


SCOPE = Scope("t", "w", "p")


class _Conn:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_thread_local_get_replaces_closed_connection():
    created: list[_Conn] = []

    def connect() -> _Conn:
        conn = _Conn()
        created.append(conn)
        return conn

    pool = ThreadLocalPsycopg(connect)
    first = pool.get()
    first.closed = True
    second = pool.get()
    assert second is not first
    assert len(created) == 2
    pool.close_all()


def test_thread_local_drop_forces_new_connection():
    created: list[_Conn] = []

    def connect() -> _Conn:
        conn = _Conn()
        created.append(conn)
        return conn

    pool = ThreadLocalPsycopg(connect)
    first = pool.get()
    pool.drop()
    assert first.closed is True
    second = pool.get()
    assert second is not first
    assert len(created) == 2
    pool.close_all()


def test_is_transient_db_error_detects_admin_shutdown():
    from code_graph_service.pg_thread_local import is_transient_db_error

    class AdminShutdown(Exception):
        pass

    assert is_transient_db_error(AdminShutdown("terminating connection due to administrator command"))
    assert is_transient_db_error(RuntimeError("Failed to read from defunct connection"))
    assert not is_transient_db_error(ValueError("bad dims"))


def test_thread_local_psycopg_one_connection_per_thread():
    created: list[_Conn] = []
    lock = threading.Lock()

    def connect() -> _Conn:
        conn = _Conn()
        with lock:
            created.append(conn)
        return conn

    pool = ThreadLocalPsycopg(connect)
    seen: dict[int, int] = {}
    barrier = threading.Barrier(4)
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            barrier.wait(timeout=5)
            a = pool.get()
            b = pool.get()
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
    pool.close_all()
    assert all(c.closed for c in created)


def test_inmemory_store_put_symbol_safe_under_threads():
    store = InMemoryStore()
    errors: list[BaseException] = []

    def _write(i: int) -> None:
        try:
            store.put_symbol(
                GraphSymbol(
                    id=f"s{i}",
                    scope=SCOPE,
                    kind=SymbolKind.FUNCTION,
                    file_path=f"f{i}.py",
                    name=f"f{i}",
                    qualified_name=f"mod.f{i}",
                    signature=f"def f{i}()",
                    body="",
                    hash_value=f"h{i}",
                    ai_documentation="",
                    doc_status=DocStatus.MISSING,
                    embedding=[],
                )
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(_write, range(40)))
    assert errors == []
    assert len(store.list_symbols(SCOPE)) == 40
