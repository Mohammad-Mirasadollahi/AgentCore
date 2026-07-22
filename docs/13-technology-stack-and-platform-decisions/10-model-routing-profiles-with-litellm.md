---
doc_id: ac.doc.stack.litellm-model-routing-profiles
title: 10 - Model Routing Profiles With LiteLLM
doc_type: standard
status: active
schema_version: '1.0'
owner: ai-platform-lead
summary: Specifies how ModelRoutingProfile maps task class and risk to LiteLLM model aliases,
  fallbacks, and offline stub behavior for AgentCore services.
tags:
- litellm
- model-routing
- llm
- configuration
phase: 13-technology-stack-and-platform-decisions
canonical_path: docs/13-technology-stack-and-platform-decisions/10-model-routing-profiles-with-litellm.md
lifecycle_lane: current
concern_lane: design
audience_lane:
- platform-engineering
- operators
authority: normative
visibility: internal
linked_symbols: []
related_docs:
- docs/13-technology-stack-and-platform-decisions/09-litellm-llm-gateway.md
- docs/13-technology-stack-and-platform-decisions/12-litellm-environment-configuration.md
- docs/07-code-knowledge-graph/05-token-optimization-and-model-routing.md
- docs/10-gap-analysis/01-gap-register.md
- .env.example
doc_version: 1.0.0
audience:
- engineer
- architect
- operator
primary_entities:
- ModelRoutingProfile
- LiteLLMGateway
- LlmCompletionPort
relations_declared:
- type: depends_on
  target: docs/13-technology-stack-and-platform-decisions/09-litellm-llm-gateway.md
- type: complements
  target: docs/07-code-knowledge-graph/05-token-optimization-and-model-routing.md
chunk_hints:
  strategy: heading_h2
  max_tokens: 700
  overlap_tokens: 48
language: en
security_classification: internal
---

# 10 - Model Routing Profiles With LiteLLM

## Purpose

Defines how AgentCore selects models **after** the LiteLLM gateway decision (`09-litellm-llm-gateway.md`). A `ModelRoutingProfile` answers *which* LiteLLM model alias to use; LiteLLM answers *how* to invoke it.

## Profile Fields

| Field | Meaning |
| --- | --- |
| `profile_id` | Stable id (tenant- or environment-scoped) |
| `task_class` | e.g. `docs.generate`, `rules.judge`, `codegen.synthesize`, `embed.symbol` |
| `risk_level` | `low` / `medium` / `high` |
| `primary_model` | LiteLLM model string (required) |
| `fallback_models` | Ordered LiteLLM aliases on primary failure |
| `max_tokens` | Hard cap for the task class |
| `timeout_ms` | Bound latency |
| `json_mode` | Required for judge / structured outputs |
| `allow_stub` | If true, services may use heuristic / `LocalEmbeddingStub` when no credentials |

## Default Task Mapping (starting point)

Operators set aliases via env (see `backend/packages/llm_gateway/README.md`). Built-in resolver: `llm_gateway.resolve_route`.

| Task class | Env override | Notes |
| --- | --- | --- |
| `docs.generate` | `AGENTCORE_LITELLM_MODEL_DOCS` | Falls back to `AGENTCORE_LITELLM_DEFAULT_MODEL`; heuristic if empty / failure |
| `rules.judge` | `AGENTCORE_LITELLM_MODEL_JUDGE` | `json_mode=true` |
| `codegen.synthesize` | `AGENTCORE_LITELLM_MODEL_CODEGEN` | Higher max_tokens at medium/high risk |
| `embed.symbol` | `AGENTCORE_LITELLM_MODEL_EMBED` | Off by default (`AGENTCORE_LITELLM_EMBEDDINGS_ENABLED=false`); stub fallback |

Risk comes from `AGENTCORE_LITELLM_RISK_LEVEL` (`low` / `medium` / `high`). Fallbacks: `AGENTCORE_LITELLM_FALLBACK_MODELS` (comma-separated).

## Resolution Order

1. Project override profile (if present).
2. Tenant default profile.
3. Environment default profile.
4. Built-in safe defaults with `allow_stub=true` for offline/dev.

## Service Obligations

- Resolve profile before calling `LlmCompletionPort` / `LlmEmbeddingPort`.
- Pass the resolved LiteLLM model alias to the adapter — do not hard-code vendor model names in use cases.
- Emit observability: `profile_id`, `task_class`, `model`, tokens, latency, tenant, project.
- On exhaustion of fallbacks: follow policy (escalate, skip docs, or fail closed for high-risk judge).

## Out of Scope

- IDE or external agent-runtime model selection (outside AgentCore process).
- Replacing pgvector storage.

## Related

- Gateway ADR: `09-litellm-llm-gateway.md`
- Token optimization: `../07-code-knowledge-graph/05-token-optimization-and-model-routing.md`
