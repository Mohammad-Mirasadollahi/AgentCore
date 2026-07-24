---
doc_id: ac.doc.project-profile.usage-profile-api
title: Usage Profile API (project-profile-service)
doc_type: contract
status: active
schema_version: '1.0'
owner: project-profile-service
summary: '| Method | Path | Purpose | |--------|------|---------| | GET | `/health` | Service
  health (used by `agentcore connect`) | | GET | `/api/v1/usage-profiles` | List catalog profile
  ids | | POST | `/api/v1/projects/{project_id}/connect/bootstrap` | Idempotent register +
  activate...'
tags:
- api
- contract
- project-profile
- usage-profile
phase: usage-profile
canonical_path: backend/services/project-profile-service/docs/usage-profile-api.md
lifecycle_lane: current
concern_lane: contract
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
doc_version: 1.0.0
updated_at: '2026-07-24'
linked_symbols: []
---

# Usage Profile API (project-profile-service)


## Purpose

| Method | Path | Purpose | |--------|------|---------| | GET | `/health` | Service health (used by `agentcore connect`) | | GET | `/api/v1/usage-profiles` | List catalog profile ids | | POST | `/api/v1/projects/{project_id}/connect/bootstrap` | Idempotent register + activate + MCP fragment (HTTP or stdio) | | POST | `/api/v1/projects/{project_id}/connect/sources` | Register server path or git.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Service health (used by `agentcore connect`) |
| GET | `/api/v1/usage-profiles` | List catalog profile ids |
| POST | `/api/v1/projects/{project_id}/connect/bootstrap` | Idempotent register + activate + MCP fragment (HTTP or stdio) |
| POST | `/api/v1/projects/{project_id}/connect/sources` | Register server path or git source |
| POST | `/api/v1/projects/{project_id}/connect/ingest` | Request graph ingest for registered source |
| GET | `/api/v1/projects/{project_id}/connect/status` | Profile, code source, ingest status |
| POST | `/api/v1/projects/{project_id}/usage-profile:activate` | Activate a Usage Profile on the project |
| GET | `/api/v1/projects/{project_id}/usage-profile/effective` | Resolve effective profile for scope |
| GET | `/api/v1/projects/{project_id}/usage-profile/cursor-mcp` | Materialize Cursor `mcpServers` fragment |

### MCP HTTP gateway (Phase B)

On the AgentCore host:

```bash
export AGENTCORE_MCP_TOKEN_SECRET='long-random-secret'
export AGENTCORE_MCP_HTTP_PUBLIC_URL='http://agentcore.example.internal:32500'
export AGENTCORE_MCP_STORE_MODE=postgres   # when Compose is up
agentcore mcp serve-http --host 0.0.0.0 --port 32500
```

Clients receive `url` + `Authorization` from bootstrap / `agentcore connect` (no SSH in mcp.json).

Register/patch project profile may also set `usage_profile`.

## Activate body

```json
{
  "usage_profile": "programming-cursor-mcp",
  "apply_catalog_defaults": true
}
```

When `apply_catalog_defaults` is true (default), domain pack and feature profile are taken from the catalog entry.

## Cursor onboarding

1. Register project (or use existing).
2. Activate `programming-cursor-mcp`.
3. GET `.../usage-profile/cursor-mcp` and merge into Cursor MCP settings.
4. Set `PYTHONPATH` so `python -m mcp_gateway_service` resolves.
5. Reload Cursor.

See `docs/08-software-engineering-architecture/35-usage-profile-and-cursor-mcp-onboarding.md`.

## Related Documents

- `backend/docs/API_NAMING_AND_CONTRACT_STANDARD.md` — HTTP naming and contract conventions
- Sibling service design docs under `docs/` for the owning phase vertical slice
