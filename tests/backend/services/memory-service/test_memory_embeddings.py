"""GAP-T03: memory embeddings SoR + Stage-1 retrieve."""

from __future__ import annotations

from dataclasses import dataclass

from memory_service.core import MemoryService, Scope
from memory_service.domain.embeddings_store import (
    InMemoryMemoryEmbeddingStore,
    MemoryEmbeddingRow,
    stage1_retrieve,
)
from memory_service.testing import InMemoryStore

SCOPE = Scope("t", "w", "p")


@dataclass
class _EmbedResult:
    vector: list[float]
    model: str
    dims: int


class _HashEmbedder:
    model = "local-hash-v1"
    dims = 8

    def embed(self, text: str, *, is_query: bool = False) -> _EmbedResult:
        _ = is_query
        # One-hot on first letter bucket so exact-title queries dominate.
        vec = [0.0] * self.dims
        key = (text.strip().lower()[:1] or " ")
        vec[ord(key) % self.dims] = 1.0
        return _EmbedResult(vec, self.model, self.dims)


def test_retrieve_by_embedding_returns_indexed_memory():
    store = InMemoryStore()
    emb = InMemoryMemoryEmbeddingStore()
    stub = _HashEmbedder()
    service = MemoryService(store, embedding_store=emb, embedder=stub)
    created = service.create_memory(
        SCOPE,
        "agent",
        "corr",
        "m1",
        {
            "kind": "semantic",
            "title": "Use dependency injection",
            "body": "Memory retrieval must use DI composition roots.",
            "tags": ["architecture"],
            "evidence_refs": ["d1"],
            "source_refs": ["s1"],
            "confidence": 0.9,
        },
    )
    service.consolidate_memory(SCOPE, "agent", "corr", "c1", [created.id], "activate")
    service.index_memory_embedding(SCOPE, created.id)
    result = service.retrieve_by_embedding(SCOPE, "Use dependency injection", top_k=3)
    assert result["hits"]
    assert result["hits"][0]["memory_id"] == created.id
    assert result["retrieval"].startswith("stage1")


def test_retrieve_context_attributes_dense_hits():
    store = InMemoryStore()
    emb = InMemoryMemoryEmbeddingStore()
    stub = _HashEmbedder()
    service = MemoryService(store, embedding_store=emb, embedder=stub)
    created = service.create_memory(
        SCOPE,
        "agent",
        "corr",
        "m1",
        {
            "kind": "semantic",
            "title": "Use dependency injection",
            "body": "Memory retrieval must use DI composition roots.",
            "tags": ["architecture"],
            "evidence_refs": ["d1"],
            "source_refs": ["s1"],
            "confidence": 0.9,
        },
    )
    service.consolidate_memory(SCOPE, "agent", "corr", "c1", [created.id], "activate")
    service.index_memory_embedding(SCOPE, created.id)
    bundle = service.retrieve_context(
        SCOPE, "agent", "corr", "Use dependency injection", token_budget=200
    )
    assert bundle.items
    dense_items = [item for item in bundle.items if "dense_retrieval" in item]
    assert dense_items
    assert dense_items[0]["dense_retrieval"]
    assert "dense=" in dense_items[0]["selection_reason"]
    events = [e for e in store.outbox() if e.get("event_type") == "ContextBundleBuilt"]
    assert events
    payload = events[-1]["payload"]
    assert payload["dense_retrieval"]["pgvector"] is True
    assert payload["dense_retrieval"]["stage"].startswith("pgvector")

def test_stage1_ranks_higher_cosine_first():
    emb = InMemoryMemoryEmbeddingStore()
    query = [1.0, 0.0, 0.0, 0.0]
    emb.upsert(
        MemoryEmbeddingRow(
            memory_id="best",
            tenant_id="t",
            workspace_id="w",
            project_id="p",
            vector=[1.0, 0.0, 0.0, 0.0],
            model="m",
            dims=4,
        )
    )
    emb.upsert(
        MemoryEmbeddingRow(
            memory_id="worse",
            tenant_id="t",
            workspace_id="w",
            project_id="p",
            vector=[0.5, 0.5, 0.0, 0.0],
            model="m",
            dims=4,
        )
    )
    hits = stage1_retrieve(emb, SCOPE, query, top_k=2)
    assert [h["memory_id"] for h in hits.hits] == ["best", "worse"]
    assert hits.hits[0]["score"] > hits.hits[1]["score"]


def test_stage1_helper_tenant_isolation():
    emb = InMemoryMemoryEmbeddingStore()
    stub = _HashEmbedder()
    emb.upsert(
        MemoryEmbeddingRow(
            memory_id="m-a",
            tenant_id="tenant-a",
            workspace_id="w",
            project_id="p",
            vector=stub.embed("alpha").vector,
            model=stub.model,
            dims=stub.dims,
        )
    )
    foreign = Scope("tenant-b", "w", "p")
    hits = stage1_retrieve(emb, foreign, stub.embed("alpha").vector, top_k=5)
    assert hits.hits == []


def test_explain_retrieval_attributes_dense_stages(monkeypatch):
    store = InMemoryStore()
    emb = InMemoryMemoryEmbeddingStore()
    service = MemoryService(store, embedder=_HashEmbedder(), embedding_store=emb)
    explanation = service.explain_retrieval(SCOPE, "alpha")
    assert explanation["dense_retrieval"]["stage1"] == "pgvector"
    assert explanation["attribution"]["pgvector"] is True
    assert "turbovec" in explanation["attribution"]

    monkeypatch.setenv("AGENTCORE_RAG_ANN_ACCELERATOR", "off")
    explanation_off = service.explain_retrieval(SCOPE, "alpha")
    assert explanation_off["dense_retrieval"]["stage2"] == "off"


def test_stage2_allowlist_when_vector_index_injected():
    from vector_index import InMemoryEntityIdMap, InMemoryVectorIndex

    emb = InMemoryMemoryEmbeddingStore()
    query = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for mid, vec in (
        ("best", [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ("other", [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ):
        emb.upsert(
            MemoryEmbeddingRow(
                memory_id=mid,
                tenant_id="t",
                workspace_id="w",
                project_id="p",
                vector=vec,
                model="m",
                dims=8,
            )
        )
    result = stage1_retrieve(
        emb,
        SCOPE,
        query,
        top_k=2,
        vector_index=InMemoryVectorIndex(dim=8),
        entity_id_map=InMemoryEntityIdMap(),
    )
    assert result.stage2_used is True
    assert result.retrieval == "stage1_pgvector+turbovec"
    assert result.hits[0]["memory_id"] == "best"
    assert result.hits[0]["retrieval"] == "stage1+turbovec"


def test_local_hash_embedder_and_migration_files():
    from pathlib import Path

    from memory_service.local_embedder import LocalHashEmbedder
    from memory_service.postgres_embeddings import MIGRATION_FILES

    emb = LocalHashEmbedder(dims=16)
    out = emb.embed("dependency injection")
    assert len(out.vector) == 16
    assert abs(sum(v * v for v in out.vector) - 1.0) < 1e-5
    root = Path(__file__).resolve().parents[4] / "backend/services/memory-service/migrations"
    assert MIGRATION_FILES == (
        "0003_memory_embeddings.sql",
        "0004_embedding_id_map.sql",
    )
    for name in MIGRATION_FILES:
        assert (root / name).is_file()
