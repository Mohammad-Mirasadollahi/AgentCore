"""Phase F2: embedding preload env knob."""

from __future__ import annotations

from code_graph_service.domain.embeddings import LocalEmbeddingStub
from code_graph_service.llm_wiring import HybridEmbeddings, maybe_preload_embeddings
from code_graph_service.local_embeddings import embedding_settings_from_env


def test_embedding_preload_flag_defaults_false():
    cfg = embedding_settings_from_env({})
    assert cfg["preload"] is False


def test_embedding_preload_flag_true():
    cfg = embedding_settings_from_env({"AGENTCORE_EMBEDDING_PRELOAD": "true"})
    assert cfg["preload"] is True


def test_maybe_preload_embeddings_calls_local_preload(monkeypatch):
    calls: list[str] = []

    class FakeLocal:
        model_name = "fake"

        def preload(self) -> None:
            calls.append("preload")

        def embed(self, text: str, *, is_query: bool = False):
            raise AssertionError("embed should not run")

    emb = HybridEmbeddings(None, local=FakeLocal(), stub=LocalEmbeddingStub(dims=8), dims=8)
    assert maybe_preload_embeddings(emb, {"AGENTCORE_EMBEDDING_PRELOAD": "1"}) is True
    assert calls == ["preload"]
    assert maybe_preload_embeddings(emb, {"AGENTCORE_EMBEDDING_PRELOAD": "false"}) is False
