"""Live Docker integration tests for code-graph stores (non-default ports)."""

from __future__ import annotations

import os
import uuid

import pytest

from code_graph_service.core import CodeGraphService, Scope
from code_graph_service.neo4j_store import Neo4jStore
from code_graph_service.postgres_store import PostgresStore

# Port profile: backend/configs/port-profiles/agentcore-dev.json
POSTGRES_PORT = int(os.environ.get("AGENTCORE_POSTGRES_PORT", "32232"))
NEO4J_BOLT_PORT = int(os.environ.get("AGENTCORE_NEO4J_BOLT_PORT", "32287"))
POSTGRES_PASSWORD = os.environ.get("AGENTCORE_POSTGRES_PASSWORD", "agentcore-local-dev-secret")
NEO4J_PASSWORD = os.environ.get("AGENTCORE_NEO4J_PASSWORD", "agentcore-local-dev-secret")
NEO4J_USER = os.environ.get("AGENTCORE_NEO4J_USER", "neo4j")

PYTHON_SOURCE = """\
def check_password(password):
    return len(password) > 8

def login(user, password):
    return check_password(password)
"""


def _require_tcp(host: str, port: int) -> None:
    import socket

    sock = socket.socket()
    sock.settimeout(2)
    try:
        sock.connect((host, port))
    except OSError as exc:
        pytest.skip(f"service not reachable at {host}:{port}: {exc}")
    finally:
        sock.close()


def _assert_non_default_ports() -> None:
    forbidden = {5432, 7474, 7687}
    assert POSTGRES_PORT not in forbidden, "Postgres host port must not be default 5432"
    assert NEO4J_BOLT_PORT not in forbidden, "Neo4j Bolt host port must not be default 7687"


def test_docker_ports_follow_port_profile():
    _assert_non_default_ports()
    _require_tcp("127.0.0.1", POSTGRES_PORT)
    _require_tcp("127.0.0.1", NEO4J_BOLT_PORT)


def test_postgres_store_python_ingest_live():
    _assert_non_default_ports()
    _require_tcp("127.0.0.1", POSTGRES_PORT)
    url = (
        f"postgresql://agentcore:{POSTGRES_PASSWORD}@127.0.0.1:{POSTGRES_PORT}/agentcore"
    )
    store = PostgresStore(url)
    scope = Scope("tenant-live", "ws-live", f"proj-{uuid.uuid4().hex[:8]}")
    service = CodeGraphService(store)
    result = service.ingest_file(
        scope,
        "agent",
        "corr-pg",
        f"idem-pg-{uuid.uuid4().hex}",
        {"file_path": "src/auth.py", "source": PYTHON_SOURCE, "language": "python"},
    )
    assert result.symbols_indexed >= 3
    login_id = f"sym:{scope.project_id}:src.auth.login"
    neighbors = service.structural_query(scope, login_id, "CALLS")
    assert any(edge["rel_type"] == "CALLS" for edge in neighbors["edges"])
    assert store.outbox()[-1]["event_type"] in {"FileIngested", "SymbolsDocumented"}


def test_neo4j_store_python_ingest_live():
    _assert_non_default_ports()
    _require_tcp("127.0.0.1", NEO4J_BOLT_PORT)
    store = Neo4jStore(
        uri=f"bolt://127.0.0.1:{NEO4J_BOLT_PORT}",
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        ensure_schema=True,
    )
    try:
        scope = Scope("tenant-live", "ws-live", f"proj-{uuid.uuid4().hex[:8]}")
        service = CodeGraphService(store)
        result = service.ingest_file(
            scope,
            "agent",
            "corr-nj",
            f"idem-nj-{uuid.uuid4().hex}",
            {"file_path": "src/auth.py", "source": PYTHON_SOURCE, "language": "python"},
        )
        assert result.symbols_indexed >= 3
        login_id = f"sym:{scope.project_id}:src.auth.login"
        neighbors = service.structural_query(scope, login_id, "CALLS")
        assert any(edge["rel_type"] == "CALLS" for edge in neighbors["edges"])
        events = store.outbox()
        assert any(event["event_type"] == "FileIngested" for event in events)
    finally:
        store.close()
