"""GAP-T03: code-graph embedding refresh under refresh-policy.json."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from code_graph_service.core import CodeGraphService, LocalEmbeddingStub, Scope
from code_graph_service.postgres_side import InMemoryEmbeddingIndex
from code_graph_service.testing import InMemoryStore

SCOPE = Scope("t", "w", "p")
POLICY = (
    Path(__file__).resolve().parents[4]
    / "backend"
    / "configs"
    / "embeddings"
    / "refresh-policy.json"
)

SOURCE = """\
def helper():
    return 1

def run():
    return helper()
"""


def _ingest(service: CodeGraphService, key: str = "k1") -> None:
    service.ingest_file(
        SCOPE,
        "agent",
        "corr",
        key,
        {"file_path": "src/mod.py", "source": SOURCE, "language": "python"},
    )


def test_refresh_embeddings_indexes_missing_rows():
    store = InMemoryStore()
    index = InMemoryEmbeddingIndex()
    service = CodeGraphService(
        store,
        embeddings=LocalEmbeddingStub(dims=16, model="local-hash-v1"),
        embedding_index=index,
    )
    _ingest(service)
    assert index.list_symbol_models(SCOPE)  # ingest already indexed
    index.wipe_scope(SCOPE)
    report = service.refresh_embeddings(SCOPE, policy_path=POLICY)
    assert report.state == "complete"
    assert report.scanned >= 2
    assert report.refreshed >= 1
    assert index.list_symbol_models(SCOPE)
    assert report.policy_id == "default-embedding-refresh"


def test_refresh_embeddings_skips_when_model_unchanged():
    store = InMemoryStore()
    index = InMemoryEmbeddingIndex()
    stub = LocalEmbeddingStub(dims=16, model="local-hash-v1")
    service = CodeGraphService(store, embeddings=stub, embedding_index=index)
    _ingest(service)
    second = service.refresh_embeddings(SCOPE, policy_path=POLICY)
    assert second.state == "complete"
    assert second.skipped >= 1
    assert second.refreshed == 0


def test_refresh_embeddings_force_and_model_mismatch():
    store = InMemoryStore()
    index = InMemoryEmbeddingIndex()
    service = CodeGraphService(
        store,
        embeddings=LocalEmbeddingStub(dims=16, model="model-a"),
        embedding_index=index,
    )
    _ingest(service)
    service.embeddings = LocalEmbeddingStub(dims=16, model="model-b")
    report = service.refresh_embeddings(SCOPE, policy_path=POLICY)
    assert report.state == "complete"
    assert report.refreshed >= 1
    assert report.reasons.get("configured_model_mismatch", 0) >= 1
    forced = service.refresh_embeddings(SCOPE, force=True, policy_path=POLICY)
    assert forced.state == "complete"
    assert forced.refreshed >= 1
    assert forced.reasons.get("operator_force_refresh", 0) >= 1


def test_refresh_embeddings_dry_run_does_not_write():
    store = InMemoryStore()
    index = InMemoryEmbeddingIndex()
    service = CodeGraphService(
        store,
        embeddings=LocalEmbeddingStub(dims=16, model="local-hash-v1"),
        embedding_index=index,
    )
    _ingest(service)
    index.wipe_scope(SCOPE)
    report = service.refresh_embeddings(SCOPE, dry_run=True, policy_path=POLICY)
    assert report.state == "complete"
    assert report.dry_run is True
    assert report.refreshed >= 1
    assert index.list_symbol_models(SCOPE) == {}


def test_refresh_embeddings_rejects_incomplete_tenant_scope():
    store = InMemoryStore()
    index = InMemoryEmbeddingIndex()
    service = CodeGraphService(
        store,
        embeddings=LocalEmbeddingStub(dims=16, model="local-hash-v1"),
        embedding_index=index,
    )
    bad = SimpleNamespace(tenant_id="", workspace_id="w", project_id="p")
    report = service.refresh_embeddings(bad, policy_path=POLICY)
    assert report.state == "failed"
    assert report.error
    assert "tenant_id" in report.error
