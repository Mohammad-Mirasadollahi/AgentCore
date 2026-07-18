"""AgentCore Code-Knowledge Graph service (Phase 7)."""

from .core import (
    CodeGraphService,
    LocalEmbeddingStub,
    language_matrix,
    supported_languages,
)

__all__ = [
    "CodeGraphService",
    "LocalEmbeddingStub",
    "language_matrix",
    "supported_languages",
]

from .core import CodeGraphService, Scope

__all__ = ["CodeGraphService", "Scope"]
