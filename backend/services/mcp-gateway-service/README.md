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
| `agentcore_code_graph_search` | read | Semantic search over the code-knowledge graph |
| `agentcore_code_graph_get_symbol` | read | Fetch one symbol by id or qualified_name |
| `agentcore_code_graph_neighbors` | read | Structural neighbors (CALLS/IMPORTS/…) |
| `agentcore_code_graph_impact` | read | Multi-hop impact neighborhood around a symbol |
| `agentcore_code_graph_explore` | read | **Primary** surgical context: seeds + call path + budgeted source |
| `agentcore_code_graph_detect_changes` | read | Risk-scored review context for changed files |
| `agentcore_code_graph_architecture_overview` | read | Communities, hubs, bridges, gaps, surprises |
| `agentcore_code_graph_path` | read | Shortest path between two symbols |
| `agentcore_code_graph_hybrid_search` | read | RRF hybrid lexical + semantic search |
| `agentcore_code_graph_freshness` | read | Pending-sync / stale banners |
| `agentcore_code_graph_sync` | write | **Preferred:** auto full vs incremental repo sync |
| `agentcore_code_graph_purge` | write | Wipe project graph (`confirm=true`); then sync |
| `agentcore_code_graph_generation_context` | read | Generation context pack for coding agents |
| `agentcore_code_graph_ingest_file` | write | Index one source file (power users) |
| `agentcore_code_graph_ingest_repo` | write | Walk a repo root (prefer `sync`) |
| `agentcore_code_graph_language_profile` | read | Polyglot language stats for the project graph |
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

**Code-graph backend** is selected separately via `AGENTCORE_MCP_GRAPH_MODE` (or auto):

| Graph mode | When | Behavior |
|------------|------|----------|
| `neo4j` | `AGENTCORE_MCP_GRAPH_MODE=neo4j`, or auto when `AGENTCORE_NEO4J_PASSWORD` is set and store is neo4j | Same composition root as `code-graph-service` (`bootstrap.build_service`) — **no toy seed** |
| `postgres` | Explicit or `AGENTCORE_CODE_GRAPH_STORE=postgres` | Postgres structural store |
| `memory` | Tests / default without Neo4j password; **also used as fallback** if Neo4j/Postgres are configured but unreachable at gateway start (ERROR logged; MCP stays up) | In-memory graph + optional demo seed |

Responses include `store_mode` and `graph_mode`.

Per-service URL overrides (optional):

- `AGENTCORE_CORE_DATA_DATABASE_URL`
- `AGENTCORE_MEMORY_DATABASE_URL`
- `AGENTCORE_CODE_GRAPH_DATABASE_URL`
- `AGENTCORE_DOCS_SYNC_DATABASE_URL`

Neo4j (when graph_mode=neo4j):

- `AGENTCORE_NEO4J_URI` / `USER` / `PASSWORD` / `DATABASE`
- `AGENTCORE_CODE_GRAPH_STORE=neo4j`
- `AGENTCORE_MCP_GRAPH_SEED=false` is implied for Neo4j (toy seed never written)

## Prerequisites

```bash
bash scripts/ensure-venv.sh
```

Apply service migrations (Compose profile `core` / `all` mounts them). For Cursor + Postgres:

```bash
export AGENTCORE_DATABASE_URL=postgresql://agentcore:secret@127.0.0.1:32232/agentcore
export AGENTCORE_MCP_STORE_MODE=postgres
# Real Neo4j code graph (same env as code-graph-service):
export AGENTCORE_NEO4J_PASSWORD=secret
export AGENTCORE_NEO4J_URI=bolt://127.0.0.1:32287
# optional force:
# export AGENTCORE_MCP_GRAPH_MODE=neo4j
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

## Run (HTTP — Phase B, concurrent agents)

```bash
export AGENTCORE_MCP_TOKEN_SECRET='long-random-secret'
export AGENTCORE_MCP_HTTP_PUBLIC_URL='http://127.0.0.1:32500'
export AGENTCORE_MCP_STORE_MODE=memory   # or postgres when Compose is up
agentcore mcp serve-http --host 0.0.0.0 --port 32500
# POST /mcp with Authorization: Bearer <scoped-or-shared-token>
```

Or: `python -m mcp_gateway_service --http --port 32500`

## Tests

```bash
PYTHONPATH=backend/services/mcp-gateway-service/src:backend/packages \
  .venv/bin/python -m pytest tests/backend/services/mcp-gateway-service -q
```

Design: `docs/08-software-engineering-architecture/35-usage-profile-and-cursor-mcp-onboarding.md`  
One-command connect: `docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md`
