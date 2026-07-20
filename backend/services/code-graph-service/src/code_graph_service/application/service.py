"""CodeGraphService facade — composes ingest, query, and generation use cases."""

from __future__ import annotations

from typing import Any

from ..domain.documentation import HeuristicDocGenerator
from ..domain.embeddings import LocalEmbeddingStub
from ..domain.freshness import FreshnessState
from ..domain.languages import assert_required_languages_supported
from ..domain.ports import Store
from ..postgres_side import EmbeddingIndex
from .generation import GenerationUseCases
from .ingest import IngestUseCases
from .intelligence import IntelligenceUseCases
from .queries import QueryUseCases


class CodeGraphService(IngestUseCases, QueryUseCases, GenerationUseCases, IntelligenceUseCases):
    """Application service entrypoint for the Code-Knowledge Graph."""

    def __init__(
        self,
        store: Store,
        docs: HeuristicDocGenerator | None = None,
        embeddings: LocalEmbeddingStub | None = None,
        embedding_index: EmbeddingIndex | None = None,
        llm: Any | None = None,
    ) -> None:
        assert_required_languages_supported()
        self.store = store
        self.docs = docs or HeuristicDocGenerator()
        self.embeddings = embeddings or LocalEmbeddingStub()
        self.embedding_index = embedding_index
        self.llm = llm
        self.freshness = FreshnessState()

    def llm_providers(self) -> list[dict[str, Any]]:
        if self.llm is None:
            return []
        return [p.to_dict() for p in self.llm.list_providers()]

    def llm_config(self) -> dict[str, Any]:
        if self.llm is None:
            return {"enabled": False, "configured": False}
        from llm_gateway.routing import (
            docs_generation_enabled,
            embeddings_generation_enabled,
            resolve_route,
        )

        settings = getattr(self.llm, "settings", None)
        default_model = getattr(settings, "default_model", "") if settings else ""
        payload = self.llm.settings_public()
        payload.update(
            {
                "docs_enabled": docs_generation_enabled(),
                "embeddings_enabled": embeddings_generation_enabled(),
                "route_docs": resolve_route("docs.generate", default_model=default_model).to_dict(),
                "route_embed": resolve_route("embed.symbol", default_model=default_model).to_dict(),
            }
        )
        return payload
