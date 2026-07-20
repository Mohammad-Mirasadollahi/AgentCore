# MCP Gateway Service

Path: `backend/services/mcp-gateway-service`

## Purpose

Exposes AgentCore capabilities to IDE clients (Cursor) over the Model Context Protocol (MCP). Tool surfaces are defined by the active **Usage Profile**. Tool calls are dispatched to **in-process** core-data, memory, code-graph, docs-sync, and common-context (Agent Workspace Guidance) service slices.

## Cursor tools (`programming-cursor-mcp`)

| Tool | Mode | Purpose |
|------|------|---------|
| `agentcore_ping` | read | Connectivity + profile metadata |
| `agentcore_get_effective_profile` | read | Effective Usage Profile |
| `agentcore_memory_retrieve` | read | Retrieve memory for a query |
| `agentcore_code_graph_search` | read | Search code-knowledge graph |
| `agentcore_create_task` | write | Create a Task |
| `agentcore_write` | write | Unified write: `memory` / `task` / `activity` / `decision` |
| `agentcore_docs_drift_check` | read | Docs drift for a symbol |
| `agentcore_docs_write` | write | Docs workflow: `validate` / `note` / `draft` / `index` |
| `agentcore_docs_status` | read | Coverage + missing docs |
| `agentcore_guidance_resolve` | read | Resolve AGENTS entry, always-on rules, skill catalog (seeds MCP-first pack) |
| `agentcore_guidance_list_skills` | read | List skill catalog descriptors |
| `agentcore_guidance_get_skill` | read | Fetch one skill body by id or name |

## Layout

| Module | Role |
|--------|------|
| `store_factory.py` | memory vs postgres store selection |
| `backends/platform.py` | `PlatformBackends` facade + seeds |
| `backends/dispatch.py` | capability router (`maps_to`) |
| `backends/writes.py` | `platform.write` (memory/task/activity/decision) |
| `backends/docs.py` | docs-sync write/status/drift helpers |
| `backends/guidance.py` | Agent Workspace Guidance resolve/list/get-skill |
| `backends/_paths.py` | PYTHONPATH bootstrap for in-process services |
| `server.py` | MCP JSON-RPC stdio surface |

| Mode | When | Behavior |
|------|------|----------|
| `memory` | Default, or `AGENTCORE_MCP_STORE_MODE=memory` | In-memory stores (tests / ephemeral IDE sessions) |
| `postgres` | `AGENTCORE_DATABASE_URL` set, or `AGENTCORE_MCP_STORE_MODE=postgres` | Shared PostgreSQL schemas with the platform services |

Per-service URL overrides (optional):

- `AGENTCORE_CORE_DATA_DATABASE_URL`
- `AGENTCORE_MEMORY_DATABASE_URL`
- `AGENTCORE_CODE_GRAPH_DATABASE_URL`
- `AGENTCORE_DOCS_SYNC_DATABASE_URL`

Responses include `store_mode` so clients can see which path is active.

## Prerequisites

```bash
bash scripts/ensure-venv.sh
```

Apply service migrations (Compose profile `core` / `all` mounts them). For Cursor + Postgres:

```bash
export AGENTCORE_DATABASE_URL=postgresql://agentcore:secret@127.0.0.1:32232/agentcore
export AGENTCORE_MCP_STORE_MODE=postgres
```

## Run (stdio for Cursor)

```bash
export AGENTCORE_USAGE_PROFILE=programming-cursor-mcp
export AGENTCORE_TENANT_ID=t
export AGENTCORE_WORKSPACE_ID=w
export AGENTCORE_PROJECT_ID=p
PYTHONPATH=backend/services/mcp-gateway-service/src:backend/packages:backend/services/core-data-service/src:backend/services/memory-service/src:backend/services/code-graph-service/src:backend/services/docs-sync-service/src \
  .venv/bin/python -m mcp_gateway_service
```

`agentcore cursor export` forwards `AGENTCORE_DATABASE_URL` / `AGENTCORE_MCP_STORE_MODE` into the generated MCP env when present.

## Tests

```bash
PYTHONPATH=backend/services/mcp-gateway-service/src:backend/packages \
  .venv/bin/python -m pytest tests/backend/services/mcp-gateway-service -q
```

Design: `docs/08-software-engineering-architecture/35-usage-profile-and-cursor-mcp-onboarding.md`
