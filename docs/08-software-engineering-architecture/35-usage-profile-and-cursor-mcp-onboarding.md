# Usage Profile and Cursor MCP Onboarding

## Purpose

A **Usage Profile** lets a person or organization shape AgentCore for a concrete job (for example software engineering with Cursor) without forking the platform. It composes existing knobs—domain pack, feature profile, connectors, and exposed MCP tools—into one named, versioned configuration that can be activated on a project and materialized into a Cursor MCP connection.

This document is the design home for Usage Profiles. It complements:

- `26-domain-customization-and-feature-control.md` (domain packs and feature profiles)
- `20-agent-and-resource-connectivity-automation.md` (connectors and connection profiles)
- `05-interoperability-ecosystem/08-agent-communication-language-and-runtime-sdk.md` (MCP as a translator bridge)

## Vocabulary

| Term | Meaning |
|------|---------|
| Usage Profile | Named composition of packs, features, connectors, and MCP tool surface for a use case |
| Feature profile | Which capabilities are enabled/hidden/approval-gated (existing concept) |
| Domain pack | Domain-oriented defaults (existing concept) |
| Connection profile | Generated client config for one connector (for example Cursor MCP) |
| MCP gateway | AgentCore process that speaks MCP to IDE clients and maps tools to platform APIs |

Usage Profiles are **not** Cursor workspace rule packs under `ai-toolstack/`. Those configure the AgentCore development IDE only.

## Goals

- Organizations can pick a profile such as `programming-cursor-mcp` and attach it to a project.
- Cursor can connect through MCP using a generated `mcp.json` fragment.
- Only tools allowed by the active Usage Profile are advertised on `tools/list`.
- Activation is scoped (tenant / workspace / project) and auditable.

## Non-goals

- Replacing Universal Agent JSON or the Phase 5 broker.
- Shipping a full Neo4j/MCP marketplace.
- Embedding Cursor-specific product logic inside every backend service.

## Schema (machine-readable)

Catalog path: `backend/configs/usage-profiles/<profile_id>.json`

Required fields:

| Field | Type | Description |
|-------|------|-------------|
| `profile_id` | string | Stable id (filename stem) |
| `version` | string | Semver-like version |
| `title` | string | Human title |
| `audience` | string | e.g. `software-engineering` |
| `domain_pack` | string | Default domain pack id |
| `feature_profile` | string | Default feature profile id |
| `connectors` | array | Connector specs (`type`, `id`, `transport`, …) |
| `mcp` | object | MCP surface (`server_name`, `tools[]`) |
| `defaults` | object | Optional scope defaults |

Each MCP tool entry:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | MCP tool name |
| `description` | string | Shown to the IDE |
| `maps_to` | string | AgentCore capability key (e.g. `memory.retrieve`) |
| `input_schema` | object | JSON Schema for tool arguments |

## Runtime ownership

| Concern | Owner |
|---------|--------|
| Catalog load/validate | `backend/packages/usage_profile/` |
| Activate on project, resolve effective profile, export Cursor config | `project-profile-service` |
| MCP stdio/JSON-RPC server and tool dispatch | `mcp-gateway-service` |
| Generic IDE/broker connectors | `adapter-service` (unchanged contract; Usage Profile may reference it) |

## Activation flow

```text
1. Operator selects usage_profile_id (e.g. programming-cursor-mcp)
2. project-profile-service stores usage_profile on the project
3. Effective profile = catalog entry + project overrides
4. Export Cursor MCP connection profile (command + env)
5. Cursor starts mcp-gateway stdio server with scope env
6. tools/list returns only profile.mcp.tools
7. tools/call maps to AgentCore capability handlers
```

## Cursor onboarding (operator steps)

1. Activate Usage Profile on the project via API (`PATCH` / activate endpoint).
2. Download or copy the generated MCP connection fragment.
3. Merge into Cursor MCP settings (user or project `mcp.json`).
4. Restart MCP / reload window.
5. Verify tools appear and a smoke `tools/call` succeeds.

Example generated fragment (shape):

```json
{
  "mcpServers": {
    "agentcore-programming": {
      "command": "python",
      "args": ["-m", "mcp_gateway_service"],
      "env": {
        "AGENTCORE_USAGE_PROFILE": "programming-cursor-mcp",
        "AGENTCORE_TENANT_ID": "<tenant>",
        "AGENTCORE_WORKSPACE_ID": "<workspace>",
        "AGENTCORE_PROJECT_ID": "<project>"
      }
    }
  }
}
```

## Security

- Scope headers / env must identify tenant, workspace, and project.
- Tools inherit feature-profile gates; disabled features are omitted from `tools/list`.
- Do not put secrets in Usage Profile JSON; inject via environment or secret managers.
- MCP gateway must refuse tools not listed in the active profile.

## Acceptance criteria

- Catalog validates required fields for every shipped profile.
- A project can activate `programming-cursor-mcp`.
- Effective profile resolution returns domain pack, feature profile, connectors, and MCP tools.
- Cursor connection materialization produces a valid `mcpServers` fragment.
- MCP gateway `tools/list` matches the profile tool set.
- Unknown tool names on `tools/call` fail closed.
- MCP tool handlers call in-process AgentCore services (memory, code-graph, core-data, docs-sync), not stub-only responses.
- MCP gateway supports `AGENTCORE_MCP_STORE_MODE=memory|postgres` (auto-postgres when `AGENTCORE_DATABASE_URL` is set) so Cursor sessions share durable store schemas with the platform.
- Tests cover catalog validation, activation, materialization, MCP protocol handlers, and wired backend calls.
- Project `.venv` is created via `scripts/ensure-venv.sh` / `requirements-dev.txt`.

## Implementation home

- Design: this file
- Catalog: `backend/configs/usage-profiles/`
- Loader: `backend/packages/usage_profile/`
- Activation API: `backend/services/project-profile-service/`
- MCP server: `backend/services/mcp-gateway-service/`
- Tests: `tests/backend/usage-profile/`, `tests/backend/mcp-gateway-service/`, extended project-profile tests
