# Config

Path: `backend/services/code-graph-service/config`

## Purpose

Placeholder directory for future non-env service assets. **Operator environment
(LiteLLM, Neo4j, embeddings, scope) is not here** — use the repository-root
`.env` (template: `.env.example`).

## Operator reference (normative)

`docs/13-technology-stack-and-platform-decisions/12-litellm-environment-configuration.md`

Related ADRs:

- `docs/13-technology-stack-and-platform-decisions/09-litellm-llm-gateway.md`
- `docs/13-technology-stack-and-platform-decisions/10-model-routing-profiles-with-litellm.md`

## How to use

1. Copy repo-root `.env.example` to `.env` (or let `install.sh` / `agentcore init` create it).
2. Edit models, keys, and store settings in that root `.env`.
3. CLI loads root `.env` automatically:

```bash
set -a && source .env && set +a
```

4. Verify: `PYTHONPATH=backend/packages python -m llm_gateway config` or `GET /api/v1/llm/config`.

## Rules

- Do not add a service-local `.env` template here; keep a single operator env at the repo root.
- When adding a new env variable, update root `.env.example` and `12-litellm-environment-configuration.md`.
