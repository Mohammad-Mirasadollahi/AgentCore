"""Unit tests for embedding index, outbox mirror, and hybrid retrieval wiring."""

from __future__ import annotations

import os
import uuid

import pytest

from code_graph_service.core import CodeGraphService, Scope
from code_graph_service.outbox_mirror_store import OutboxMirrorStore
from code_graph_service.postgres_side import InMemoryEmbeddingIndex, PostgresEmbeddingIndex, PostgresOutboxMirror
from code_graph_service.testing import InMemoryStore

PYTHON_SOURCE = """\
def check_password(password):
    return len(password) > 8

def login(user, password):
    return check_password(password)
"""

POSTGRES_PORT = int(os.environ.get("AGENTCORE_POSTGRES_PORT", "32232"))
POSTGRES_PASSWORD = os.environ.get("AGENTCORE_POSTGRES_PASSWORD", "agentcore-local-dev-secret")
NEO4J_BOLT_PORT = int(os.environ.get("AGENTCORE_NEO4J_BOLT_PORT", "32287"))
NEO4J_PASSWORD = os.environ.get("AGENTCORE_NEO4J_PASSWORD", "agentcore-local-dev-secret")
NEO4J_USER = os.environ.get("AGENTCORE_NEO4J_USER", "neo4j")


def test_inmemory_embedding_index_semantic_search():
    store = InMemoryStore()
    index = InMemoryEmbeddingIndex()
    service = CodeGraphService(store, embedding_index=index)
    scope = Scope("t", "w", "emb-mem")
    service.ingest_file(
        scope,
        "agent",
        "c",
        "idem-emb",
        {"file_path": "src/auth.py", "source": PYTHON_SOURCE, "language": "python"},
    )
    hits = service.semantic_search(scope, "login password check")
    assert hits
    assert hits[0]["score"] > 0
    assert hits[0]["retrieval"] == "pgvector"
    assert "graph_neighbors" in hits[0]
    names = {hit["symbol"]["qualified_name"] for hit in hits}
    assert any("login" in name or "check_password" in name for name in names)
    # FILE symbols must not pollute ANN index.
    assert all(hit["symbol"]["kind"] != "file" for hit in hits)


def test_embedding_index_skips_file_kind_and_deletes_stale():
    index = InMemoryEmbeddingIndex()
    scope = Scope("t", "w", "stale")
    index.upsert(scope, "file:x", [0.1] * 16, model="local-hash-v1", kind="file")
    index.upsert(scope, "sym:fn", [0.2] * 16, model="local-hash-v1", kind="function")
    hits = index.search(scope, [0.2] * 16, top_k=5)
    assert [sid for sid, _ in hits] == ["sym:fn"]
    index.delete(scope, "sym:fn")
    assert index.search(scope, [0.2] * 16, top_k=5) == []


def test_generation_context_includes_expansion_field():
    store = InMemoryStore()
    service = CodeGraphService(store)
    scope = Scope("t", "w", "gen-exp")
    service.ingest_file(
        scope,
        "agent",
        "c",
        "idem-gen",
        {"file_path": "src/auth.py", "source": PYTHON_SOURCE, "language": "python"},
    )
    login_id = f"sym:{scope.project_id}:src.auth.login"
    ctx = service.build_generation_context(scope, login_id)
    assert ctx["expansion"] == "one_hop"
    assert ctx["uses_full_repository"] is False
    assert ctx["symbol_count"] >= 1


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


def test_postgres_embedding_index_live():
    _require_tcp("127.0.0.1", POSTGRES_PORT)
    url = f"postgresql://agentcore:{POSTGRES_PASSWORD}@127.0.0.1:{POSTGRES_PORT}/agentcore"
    index = PostgresEmbeddingIndex(url, dims=16, ensure_schema=True)
    try:
        store = InMemoryStore()
        service = CodeGraphService(store, embedding_index=index)
        scope = Scope("tenant-emb", "ws-emb", f"proj-{uuid.uuid4().hex[:8]}")
        service.ingest_file(
            scope,
            "agent",
            "c",
            f"idem-{scope.project_id}",
            {"file_path": "src/auth.py", "source": PYTHON_SOURCE, "language": "python"},
        )
        hits = service.semantic_search(scope, "authenticate login")
        assert hits
        assert hits[0]["score"] > 0
        assert hits[0]["retrieval"] == "pgvector"
        assert all(hit["symbol"]["kind"] != "file" for hit in hits)
    finally:
        index.close()


def test_hybrid_pgvector_and_inmemory_graph_neighbors():
    """Stage-1 hybrid: pgvector-filtered hits + graph_neighbors from structural store."""
    store = InMemoryStore()
    index = InMemoryEmbeddingIndex()
    service = CodeGraphService(store, embedding_index=index)
    scope = Scope("t", "w", "hybrid-neigh")
    service.ingest_file(
        scope,
        "agent",
        "c",
        "idem-hybrid",
        {"file_path": "src/auth.py", "source": PYTHON_SOURCE, "language": "python"},
    )
    hits = service.semantic_search(scope, "login", top_k=3, expand_seeds=2, expand_depth=1)
    assert hits
    assert any(hit.get("graph_neighbors") for hit in hits[:2])
    assert any(hit.get("graph_expansion") for hit in hits[:2])


def test_neo4j_outbox_mirrors_to_postgres_live():
    _require_tcp("127.0.0.1", POSTGRES_PORT)
    _require_tcp("127.0.0.1", NEO4J_BOLT_PORT)
    from code_graph_service.neo4j_store import Neo4jStore

    url = f"postgresql://agentcore:{POSTGRES_PASSWORD}@127.0.0.1:{POSTGRES_PORT}/agentcore"
    nj = Neo4jStore(
        uri=f"bolt://127.0.0.1:{NEO4J_BOLT_PORT}",
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        ensure_schema=True,
    )
    mirror = PostgresOutboxMirror(url)
    store = OutboxMirrorStore(nj, mirror)
    try:
        service = CodeGraphService(store)
        scope = Scope("tenant-obx", "ws-obx", f"proj-{uuid.uuid4().hex[:8]}")
        service.ingest_file(
            scope,
            "agent",
            "c",
            f"idem-obx-{scope.project_id}",
            {"file_path": "src/auth.py", "source": PYTHON_SOURCE, "language": "python"},
        )
        neo_events = [e for e in nj.outbox() if e.get("project_id") == scope.project_id]
        assert neo_events
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_id, event_type, published_at
                    FROM code_graph.outbox
                    WHERE payload->>'project_id' = %s
                    ORDER BY created_at
                    """,
                    (scope.project_id,),
                )
                rows = cur.fetchall()
        assert rows
        assert any(row["event_type"] in {"FileIngested", "SymbolsDocumented"} for row in rows)
        assert all(row["published_at"] is None for row in rows)
    finally:
        store.close()
