# LLM Gateway (LiteLLM)

Path: `backend/packages/llm_gateway`

## Purpose

Shared LiteLLM adapter for AgentCore services. Implements the stack ADR
`docs/13-technology-stack-and-platform-decisions/09-litellm-llm-gateway.md`.

## Environment

**Full operator reference (every variable, change impact, worked examples):**  
[`docs/13-technology-stack-and-platform-decisions/12-litellm-environment-configuration.md`](../../../docs/13-technology-stack-and-platform-decisions/12-litellm-environment-configuration.md)

**Copy template with inline comments:**  
`backend/services/code-graph-service/config/code-graph-service.example.env`

| Variable | Default | Meaning |
| --- | --- | --- |
| `AGENTCORE_LITELLM_ENABLED` | `true` | Master switch |
| `AGENTCORE_LITELLM_HOST` | `127.0.0.1` | Host for **auto** Base URL |
| `AGENTCORE_LITELLM_PORT` | profile `32400` | Port for **auto** Base URL |
| `AGENTCORE_LITELLM_API_BASE` | _(empty)_ | Optional Base URL **override** (if set, replaces auto) |
| `LITELLM_API_BASE` | _(empty)_ | Alias override when `AGENTCORE_LITELLM_API_BASE` unset |
| `AGENTCORE_LITELLM_API_KEY` | _(empty)_ | Gateway/proxy key (falls back to `LITELLM_API_KEY` / `OPENROUTER_API_KEY` / `OPENAI_API_KEY`) |
| `AGENTCORE_LITELLM_DEFAULT_MODEL` | _(empty)_ | Default LiteLLM model alias |
| `AGENTCORE_LITELLM_TIMEOUT_SECONDS` | `180` | Request timeout |
| `AGENTCORE_LITELLM_NUM_RETRIES` | `3` | LiteLLM `num_retries` |
| `AGENTCORE_LITELLM_RPM` | `30` | Max requests per rolling minute (client-side limiter) |
| `AGENTCORE_LITELLM_DROP_PARAMS` | `true` | `litellm.drop_params` |
| `AGENTCORE_LITELLM_REASONING_ENABLED` | `false` | Send OpenRouter-style `reasoning.enabled` via `extra_body` |
| `AGENTCORE_LITELLM_REASONING_EFFORT` | _(empty)_ | Optional `reasoning.effort` when enabled |
| `AGENTCORE_LITELLM_DOCS_ENABLED` | `true` | Use LiteLLM for symbol docs (heuristic fallback) |
| `AGENTCORE_LITELLM_EMBEDDINGS_ENABLED` | `false` | Use LiteLLM embeddings (stub fallback; vectors reduced to 16-d) |
| `AGENTCORE_LITELLM_MODEL_DOCS` / `_EMBED` / `_JUDGE` / `_CODEGEN` | _(empty)_ | Per-task model overrides |
| `AGENTCORE_LITELLM_FALLBACK_MODELS` | _(empty)_ | Comma-separated fallback aliases |
| `AGENTCORE_LITELLM_RISK_LEVEL` | `low` | Routing risk: `low` / `medium` / `high` |
| `AGENTCORE_LITELLM_PROFILE_ID` | `env-default` | Route profile label |

Auto Base URL: `http://{HOST}:{PORT}` when no override is set.

## CLI

```bash
PYTHONPATH=backend/packages .venv/bin/python -m llm_gateway providers
PYTHONPATH=backend/packages .venv/bin/python -m llm_gateway config
PYTHONPATH=backend/packages .venv/bin/python -m llm_gateway complete --prompt "ping"
PYTHONPATH=backend/packages .venv/bin/python -m llm_gateway complete --prompt "ping" --reasoning
```

## Status

Implemented: `RpmSessionGate` tracks session start/end and in-flight count;
`LiteLlmGateway` / `FakeLlmGateway` acquire/release around `complete`/`embed`.
Observability: `gateway.rpm_sessions_snapshot()`, HTTP `GET /api/v1/llm/sessions`,
CLI `agentcore llm sessions`. Design pack:
[`docs/07-code-knowledge-graph/37-rpm-session-parallel-sync-feature-specification.md`](../../../docs/07-code-knowledge-graph/37-rpm-session-parallel-sync-feature-specification.md)
through `40`.
