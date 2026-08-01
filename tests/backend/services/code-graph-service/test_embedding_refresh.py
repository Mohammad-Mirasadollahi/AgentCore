"""GAP-T03: code-graph embedding refresh under refresh-policy.json."""

from __future__ import annotations

from pathlib import Path
import threading
import time
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
    events: list[dict] = []
    report = service.refresh_embeddings(
        SCOPE, policy_path=POLICY, on_progress=events.append
    )
    assert report.state == "complete"
    assert report.scanned >= 2
    assert report.refreshed >= 1
    assert index.list_symbol_models(SCOPE)
    assert report.policy_id == "default-embedding-refresh"
    assert events
    assert events[0]["phase"] == "embeddings"
    assert events[0]["status"] == "started"
    assert events[-1]["status"] == "finished"
    assert events[-1]["done"] == report.refreshed


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


def test_noop_repo_ingest_backfills_missing_embeddings(tmp_path):
    source = tmp_path / "mod.py"
    source.write_text(SOURCE, encoding="utf-8")
    index = InMemoryEmbeddingIndex()
    service = CodeGraphService(
        InMemoryStore(),
        embeddings=LocalEmbeddingStub(dims=16, model="local-hash-v1"),
        embedding_index=index,
    )
    first = service.ingest_repo(
        SCOPE,
        "agent",
        "corr-1",
        "repo-1",
        {"root_path": str(tmp_path)},
    )
    assert first.embedding_refresh["state"] == "complete"
    index.wipe_scope(SCOPE)

    second = service.ingest_repo(
        SCOPE,
        "agent",
        "corr-2",
        "repo-2",
        {"root_path": str(tmp_path)},
    )

    assert second.files_ingested == 0
    assert second.embedding_refresh["state"] == "complete"
    assert second.embedding_refresh["refreshed"] >= 1
    assert index.list_symbol_models(SCOPE)


def test_refresh_embeddings_uses_batch_api():
    class BatchStub(LocalEmbeddingStub):
        calls = 0

        def embed_many(self, texts, *, is_query=False):
            self.calls += 1
            return super().embed_many(texts, is_query=is_query)

    index = InMemoryEmbeddingIndex()
    stub = BatchStub(dims=16)
    service = CodeGraphService(InMemoryStore(), embeddings=stub, embedding_index=index)
    _ingest(service)
    index.wipe_scope(SCOPE)
    calls_before_refresh = stub.calls
    report = service.refresh_embeddings(SCOPE, policy_path=POLICY)
    assert report.state == "complete"
    assert report.refreshed >= 2
    assert stub.calls == calls_before_refresh + 1


def test_refresh_embeddings_runs_large_batches_with_bounded_parallelism(
    monkeypatch,
):
    monkeypatch.setenv("AGENTCORE_EMBEDDING_REFRESH_WORKERS", "3")
    class SlowBatchStub(LocalEmbeddingStub):
        def __init__(self) -> None:
            super().__init__(dims=16)
            self.active = 0
            self.peak = 0
            self.lock = threading.Lock()

        def embed_many(self, texts, *, is_query=False):
            with self.lock:
                self.active += 1
                self.peak = max(self.peak, self.active)
            try:
                time.sleep(0.02)
                return super().embed_many(texts, is_query=is_query)
            finally:
                with self.lock:
                    self.active -= 1

    source = "\n\n".join(
        f"def function_{index}():\n    return {index}" for index in range(270)
    )
    index = InMemoryEmbeddingIndex()
    stub = SlowBatchStub()
    service = CodeGraphService(
        InMemoryStore(),
        embeddings=stub,
        embedding_index=index,
    )
    service.ingest_file(
        SCOPE,
        "agent",
        "corr-large-batch",
        "large-batch",
        {"file_path": "src/large_batch.py", "source": source, "language": "python"},
    )
    index.wipe_scope(SCOPE)
    stub.peak = 0

    report = service.refresh_embeddings(SCOPE, policy_path=POLICY)

    assert report.state == "complete"
    assert report.refreshed >= 540
    assert stub.peak >= 2
    assert stub.peak <= 3
