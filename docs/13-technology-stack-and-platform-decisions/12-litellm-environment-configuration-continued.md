---
doc_id: ac.doc.stack.litellm-environment-configuration-continued
title: 12 - LiteLLM Environment Configuration (Continued)
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-docs
summary: Continuation of `docs/13-technology-stack-and-platform-decisions/12-litellm-environment-configuration.md`
  — remaining sections after the soft size budget.
tags:
- standard
- stack
phase: 13-technology-stack-and-platform-decisions
canonical_path: docs/13-technology-stack-and-platform-decisions/12-litellm-environment-configuration-continued.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols: []
---

# 12 - LiteLLM Environment Configuration (Continued)

## Purpose

Continuation of `docs/13-technology-stack-and-platform-decisions/12-litellm-environment-configuration.md` — remaining sections after the soft size budget.

## Routing And Feature Flags

### `AGENTCORE_LITELLM_RISK_LEVEL`

| | |
| --- | --- |
| **Purpose** | Risk dimension for `resolve_route` (`low` / `medium` / `high`). |
| **Default** | `low` |
| **If `high`** | Some tasks set `allow_stub=false` (fail instead of silent heuristic when models exhaust). Larger `max_tokens` for docs/codegen. |
| **If invalid** | Treated as `low`. |

### `AGENTCORE_LITELLM_PROFILE_ID`

| | |
| --- | --- |
| **Purpose** | Opaque profile label on resolved routes (config dump / future telemetry). |
| **Default** | `env-default` |
| **If changed** | Does not change model selection by itself; only identity metadata. |

### `AGENTCORE_LITELLM_DOCS_ENABLED`

| | |
| --- | --- |
| **Purpose** | Whether ingest uses LiteLLM for changed-symbol documentation. |
| **Default** | `true` |
| **If `true`** | `LlmBackedDocGenerator` tries routed models, then heuristic on failure/empty. |
| **If `false`** | Always `HeuristicDocGenerator` — no LLM cost for docs. |

**Example — force deterministic docs in a PR environment:**

```bash
AGENTCORE_LITELLM_DOCS_ENABLED=false
## Ingest still indexes symbols; ai_documentation text is heuristic-only.
```

### Local embedding variables (`AGENTCORE_EMBEDDING_*`)

Stage-1 production path uses a **local** SentenceTransformer model. Model weights are cached under `/opt/agentcore-models` so relocating the AgentCore checkout does not delete them.

| Variable | Purpose | Default |
| --- | --- | --- |
| `AGENTCORE_EMBEDDING_PROVIDER` | `local_bge` / `stub` / `litellm` | `local_bge` |
| `AGENTCORE_EMBEDDING_LOCAL_ENABLED` | Load local SentenceTransformer | `true` |
| `AGENTCORE_EMBEDDING_MODEL` | Hugging Face model id | `BAAI/bge-large-en-v1.5` |
| `AGENTCORE_EMBEDDING_CACHE_DIR` | HF + sentence-transformers cache root | `/opt/agentcore-models` |
| `AGENTCORE_EMBEDDING_DIMS` | pgvector column width (must match model) | `1024` |
| `AGENTCORE_EMBEDDING_DEVICE` | `cpu` / `cuda` / `mps` | `cpu` |

Install the optional extra once: `pip install -e '.[embeddings]'` (or `sentence-transformers`).

**Example:**

```bash
AGENTCORE_EMBEDDING_PROVIDER=local_bge
AGENTCORE_EMBEDDING_LOCAL_ENABLED=true
AGENTCORE_EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
AGENTCORE_EMBEDDING_CACHE_DIR=/opt/agentcore-models
AGENTCORE_EMBEDDING_DIMS=1024
AGENTCORE_EMBEDDING_DEVICE=cpu
```

### `AGENTCORE_LITELLM_EMBEDDINGS_ENABLED`

| | |
| --- | --- |
| **Purpose** | Whether `HybridEmbeddings` calls LiteLLM when local BGE is disabled. |
| **Default** | `false` |
| **If local BGE enabled** | LiteLLM embed path is skipped; local 1024-d vectors are used. |
| **If `true` and local off** | LiteLLM embedding model is called; vector is projected to `AGENTCORE_EMBEDDING_DIMS`. Wrong/non-embedding model → fallback to stub when `allow_stub`. |

**Example:**

```bash
AGENTCORE_EMBEDDING_LOCAL_ENABLED=false
AGENTCORE_LITELLM_EMBEDDINGS_ENABLED=true
AGENTCORE_LITELLM_MODEL_EMBED=text-embedding-3-small
```

### Task model overrides

| Variable | Task class | If empty | If set |
| --- | --- | --- | --- |
| `AGENTCORE_LITELLM_MODEL_DOCS` | `docs.generate` | Uses `DEFAULT_MODEL` | That alias for documentation only |
| `AGENTCORE_LITELLM_MODEL_EMBED` | `embed.symbol` | Uses `DEFAULT_MODEL` | Embedding-only alias |
| `AGENTCORE_LITELLM_MODEL_JUDGE` | `rules.judge` | Uses `DEFAULT_MODEL` | Judge/JSON path |
| `AGENTCORE_LITELLM_MODEL_CODEGEN` | `codegen.synthesize` | Uses `DEFAULT_MODEL` | Stronger codegen alias |

**Example — cheap docs, strong judge:**

```bash
AGENTCORE_LITELLM_DEFAULT_MODEL=ollama/qwen2.5-coder
AGENTCORE_LITELLM_MODEL_DOCS=ollama/qwen2.5-coder
AGENTCORE_LITELLM_MODEL_JUDGE=gpt-4o
## Docs stay local/cheap; judge uses cloud when rule-engine calls that route.
```

### `AGENTCORE_LITELLM_FALLBACK_MODELS`

| | |
| --- | --- |
| **Purpose** | Ordered fallback aliases after primary fails (comma or semicolon separated). |
| **Default** | empty |
| **If set** | Each alias is tried in order for that request (docs/embed/complete path). |
| **If empty** | Only the primary model is attempted. |

**Example:**

```bash
AGENTCORE_LITELLM_MODEL_DOCS=gpt-4o
AGENTCORE_LITELLM_FALLBACK_MODELS=gpt-4o-mini,ollama/llama3.2
## gpt-4o fails → try gpt-4o-mini → try ollama/llama3.2 → heuristic if allow_stub.
```

---

## Provider Credential Variables (optional)

These are not required for gateway boot. They mark providers `configured=true` in `/api/v1/llm/providers` and authenticate vendor backends.

| Variable | Typical effect if set | If unset |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI models + fallback key for gateway | OpenAI calls fail auth |
| `ANTHROPIC_API_KEY` | Anthropic models | Anthropic unavailable |
| `AZURE_API_KEY` / `AZURE_API_BASE` / `AZURE_API_VERSION` | Azure OpenAI deployments | Azure unavailable |
| `OLLAMA_API_BASE` | Points LiteLLM at local Ollama (e.g. `http://127.0.0.1:11434`) | Default Ollama locality assumptions |
| `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `DEEPSEEK_API_KEY` | Respective providers | Those providers `configured=false` |
| `LITELLM_API_BASE` / `LITELLM_API_KEY` | Aliases for AgentCore Base URL / key when AgentCore-prefixed vars empty | Ignored if AgentCore vars set |

**Example — local Ollama only:**

```bash
AGENTCORE_LITELLM_API_BASE=
AGENTCORE_LITELLM_HOST=127.0.0.1
AGENTCORE_LITELLM_PORT=32400
AGENTCORE_LITELLM_DEFAULT_MODEL=ollama/qwen2.5-coder
OLLAMA_API_BASE=http://127.0.0.1:11434
## Ensure a LiteLLM proxy or compatible endpoint is reachable at auto Base URL,
## or set AGENTCORE_LITELLM_API_BASE to the Ollama OpenAI-compatible URL your stack uses.
```

---

## Worked Scenarios

### Scenario A — Safe local defaults (recommended starting point)

```bash
AGENTCORE_LITELLM_ENABLED=true
AGENTCORE_LITELLM_DOCS_ENABLED=true
AGENTCORE_LITELLM_EMBEDDINGS_ENABLED=false
AGENTCORE_LITELLM_DEFAULT_MODEL=ollama/qwen2.5-coder
AGENTCORE_LITELLM_TIMEOUT_SECONDS=180
AGENTCORE_LITELLM_NUM_RETRIES=3
AGENTCORE_LITELLM_RPM=30
```

**Result:** Docs may call LiteLLM; embeddings stay stub; rate limit 30/min; 180s timeout.

### Scenario B — No model calls during ingest

```bash
AGENTCORE_LITELLM_ENABLED=false
## or
AGENTCORE_LITELLM_DOCS_ENABLED=false
AGENTCORE_LITELLM_EMBEDDINGS_ENABLED=false
```

**Result:** Fully deterministic documentation and embeddings; gateway complete API returns errors if enabled=false.

### Scenario C — Cloud docs with fallback and tight RPM

```bash
AGENTCORE_LITELLM_API_BASE=https://api.openai.com/v1
AGENTCORE_LITELLM_API_KEY=sk-...
AGENTCORE_LITELLM_MODEL_DOCS=gpt-4o-mini
AGENTCORE_LITELLM_FALLBACK_MODELS=gpt-4o-mini
AGENTCORE_LITELLM_RPM=15
AGENTCORE_LITELLM_TIMEOUT_SECONDS=60
```

**Result:** Docs use OpenAI-compatible Base URL; waits if more than 15 calls/minute; fails faster than default timeout.

### Scenario D — Local BGE embeddings (recommended)

```bash
AGENTCORE_EMBEDDING_PROVIDER=local_bge
AGENTCORE_EMBEDDING_LOCAL_ENABLED=true
AGENTCORE_EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
AGENTCORE_EMBEDDING_CACHE_DIR=/opt/agentcore-models
AGENTCORE_EMBEDDING_DIMS=1024
AGENTCORE_CODE_GRAPH_DATABASE_URL=postgresql://agentcore:secret@127.0.0.1:32232/agentcore
```

**Result:** Ingest upserts 1024-d BGE vectors into `code_graph.symbol_embeddings`. Without the database URL, vectors may compute but are not persisted to pgvector.

### Scenario E — Enable semantic embeddings via LiteLLM

```bash
AGENTCORE_EMBEDDING_LOCAL_ENABLED=false
AGENTCORE_LITELLM_EMBEDDINGS_ENABLED=true
AGENTCORE_LITELLM_MODEL_EMBED=text-embedding-3-small
AGENTCORE_CODE_GRAPH_DATABASE_URL=postgresql://agentcore:secret@127.0.0.1:32232/agentcore
```

**Result:** Ingest projects LiteLLM vectors to `AGENTCORE_EMBEDDING_DIMS` for pgvector persistence.

---

## Failure Modes And Recovery

| Symptom | Likely misconfiguration | Recovery |
| --- | --- | --- |
| Startup: Neo4j password required | Empty `AGENTCORE_NEO4J_PASSWORD` with store=neo4j | Set password |
| Connection refused to `:32400` | Auto Base URL but no proxy listening | Start proxy or set `AGENTCORE_LITELLM_API_BASE` |
| Opaque LiteLLM error / “turn on debug” hint | Provider error mapped by LiteLLM; tip not suppressed | Gateway sets `suppress_debug_info`; use `AGENTCORE_LITELLM_DEBUG=true` for traces |
| Sync hangs / Ctrl+C does not exit | Workers blocked in provider HTTP; pool waited forever | Cancel waits ≤15s then abandons stuck workers; quota circuit stops further LLM calls |
| OpenRouter `429` / `free-models-per-day` | Free-tier daily quota exhausted | Wait for daily reset, switch model/key, or set `AGENTCORE_LITELLM_DOCS_ENABLED=false` |
| Docs always heuristic | `DOCS_ENABLED=false`, or `ENABLED=false`, or empty models | Enable flags and set `DEFAULT_MODEL` / `MODEL_DOCS` |
| Embeddings unchanged after enabling LLM | `EMBEDDINGS_ENABLED` still false or no DB URL | Set flag + model + database URL |
| Calls stall under load | Low `RPM` | Raise RPM or batch fewer calls |
| Auth 401 | Missing API key for provider | Set `AGENTCORE_LITELLM_API_KEY` or provider key |
| Model errors about reasoning / empty weird output on gpt-oss | `REASONING_ENABLED=false` | Set `AGENTCORE_LITELLM_REASONING_ENABLED=true` |
| Provider rejects `reasoning` field | Reasoning on for a non-reasoning model | Set `REASONING_ENABLED=false` or override per call |

## Security And Privacy Constraints

- Never commit real API keys; `.env.example` uses empty or placeholder values.
- `/api/v1/llm/config` and `python -m llm_gateway config` expose only `api_key_configured` boolean, not the secret.
- Prefer proxy mode in shared environments so vendor keys stay on the proxy host.

## Observability And Diagnostics

- Public config: `GET /api/v1/llm/config` includes timeout, retries, rpm, docs/embeddings flags, and resolved `route_docs` / `route_embed`.
- Provider inventory: `GET /api/v1/llm/providers`.
- Correlate ingest latency spikes with RPM waits and timeout settings.

## Testing And Verification

- Unit tests may use `FakeLlmGateway` without network.
- Live verification: set real Base URL/model and call `POST /api/v1/llm/complete` or `python -m llm_gateway complete --prompt "ping"`.
- Operators should confirm `api_base_is_auto` vs override via config endpoint after deploy.

## Rollout And Migration Notes

1. Copy repo-root `.env.example` to `.env` (or use `install.sh` / `agentcore init`).
2. Start with `AGENTCORE_LITELLM_EMBEDDINGS_ENABLED=false` and local/default model.
3. Enable docs LLM only after Base URL and keys work via `complete`.
4. Enable embeddings only with Postgres URL and an embedding-capable model alias.

## Engineering Acceptance Criteria

- Every variable in `.env.example` is described in this document.
- Changing Base URL override clearly disables auto host/port for request routing.
- Defaults match runtime: timeout `180`, retries `3`, rpm `30`.
- Disabling LiteLLM or docs/embeddings never breaks structural Neo4j/Postgres ingest.

## Product Acceptance Criteria

- An operator can configure LiteLLM from the root `.env.example` without reading Python source.
- Misconfiguration symptoms map to a recovery row in Failure Modes.

## Open Gaps

- Per-tenant profile tables beyond env (future control-plane UI).
- Separate RPM budgets per task class (today one process-wide limiter).


## Related Documents

- Parent document: `docs/13-technology-stack-and-platform-decisions/12-litellm-environment-configuration.md`
