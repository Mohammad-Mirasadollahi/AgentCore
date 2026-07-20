# Config

Path: `backend/services/code-graph-service/config`

## Purpose

Service-specific configuration templates for `code-graph-service` (structural store + LiteLLM).

## Files

| File | Role |
| --- | --- |
| `code-graph-service.example.env` | Copy template; every variable has inline comments (purpose + change impact) |
| This README | Boundary notes |

## Operator reference (normative)

Full behavioral contract with worked examples (“if you change X, Y happens”):

`docs/13-technology-stack-and-platform-decisions/12-litellm-environment-configuration.md`

Related ADRs:

- `docs/13-technology-stack-and-platform-decisions/09-litellm-llm-gateway.md`
- `docs/13-technology-stack-and-platform-decisions/10-model-routing-profiles-with-litellm.md`

## How to use

1. Copy `code-graph-service.example.env` to an untracked local env file (do not commit secrets), or use `config/.env` (gitignored).
2. Set `AGENTCORE_NEO4J_PASSWORD` and optional LiteLLM / OpenRouter keys.
3. Load into the process environment before start, for example:

```bash
set -a && source backend/services/code-graph-service/config/.env && set +a
```

4. Verify public settings: `PYTHONPATH=backend/packages python -m llm_gateway config` or `GET /api/v1/llm/config`.

## Modular Boundary

This directory is part of the AgentCore backend modular architecture. It must expose behavior through documented contracts, public interfaces, configuration, or events. It must not import private internals from sibling modules.

## Rules

- Keep ownership clear and local to this boundary.
- Do not hard-code ports, credentials, tenant IDs, project IDs, model names, provider endpoints, or feature behavior in application code when an env knob exists.
- Prefer dependency inversion: domain and application logic should not depend on infrastructure implementation details.
- Use shared packages only for stable contracts or cross-cutting primitives (`backend/packages/llm_gateway`).
- When adding a new env variable, update both the example env comments and `12-litellm-environment-configuration.md`.
