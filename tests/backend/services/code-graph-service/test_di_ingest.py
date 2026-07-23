"""Integration: ingest emits di_injection CALLS for FastAPI Depends."""

from __future__ import annotations

from code_graph_service.application.service import CodeGraphService
from code_graph_service.domain.models import Scope
from code_graph_service.testing import InMemoryStore


def test_ingest_emits_di_injection_edge():
    store = InMemoryStore()
    svc = CodeGraphService(store)
    scope = Scope("t", "w", "p-di")
    source = """
from fastapi import Depends

def get_db():
    return 1

def read_item(db = Depends(get_db)):
    return db
"""
    svc.ingest_file(
        scope,
        actor_id="test",
        correlation_id="c1",
        idempotency_key="k1",
        payload={"file_path": "api.py", "source": source, "language": "python"},
    )
    edges = [
        e
        for e in store.list_edges(scope)
        if e.rel_type == "CALLS" and (e.metadata or {}).get("provenance") == "di_injection"
    ]
    assert edges, "expected di_injection CALLS edge"
    assert edges[0].confidence.value == "probable"
    assert edges[0].metadata.get("framework") == "fastapi"
