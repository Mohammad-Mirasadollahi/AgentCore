"""AgentCore LiteLLM gateway — provider-agnostic LLM port + env settings."""

from __future__ import annotations

from .gateway import FakeLlmGateway, LiteLlmGateway, LlmGateway
from .providers import list_providers
from .routing import RouteDecision, docs_generation_enabled, embeddings_generation_enabled, resolve_route
from .settings import LlmGatewaySettings, build_reasoning_payload, resolve_api_base
from .types import ChatMessage, CompletionRequest, CompletionResult, EmbeddingResult, ProviderInfo

__all__ = [
    "ChatMessage",
    "CompletionRequest",
    "CompletionResult",
    "EmbeddingResult",
    "FakeLlmGateway",
    "LiteLlmGateway",
    "LlmGateway",
    "LlmGatewaySettings",
    "ProviderInfo",
    "RouteDecision",
    "build_reasoning_payload",
    "docs_generation_enabled",
    "embeddings_generation_enabled",
    "list_providers",
    "resolve_api_base",
    "resolve_route",
]
