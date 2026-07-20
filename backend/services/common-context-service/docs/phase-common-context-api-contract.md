# AgentCore Common Context API Contract

Vertical slice for `common-context-service`.

- Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`
- Idempotency: `Idempotency-Key` on mutating propose routes
- Persistence target env: `AGENTCORE_COMMON_CONTEXT_DATABASE_URL`
- Tests: `tests/backend/services/common-context-service/`

## Common items

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/projects/{project_id}/common-items` | Propose; optional `item_type` (`general`, `agents_entry`, `always_rule`, `skill`) |
| `POST` | `/api/v1/projects/{project_id}/common-items/{item_id}:approve` | Approve; enforces one `agents_entry` and unique skill `name` |
| `POST` | `/api/v1/projects/{project_id}/common-items/{item_id}:suppress` | Suppress |
| `POST` | `/api/v1/projects/{project_id}/common-items/{item_id}:reject` | Reject |
| `GET` | `/api/v1/projects/{project_id}/common-context/bundle` | Generic score/budget resolve |

## Agent Workspace Guidance

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/projects/{project_id}/guidance/resolve` | AWG bundle (entry, always rules, skill catalog) |
| `GET` | `/api/v1/projects/{project_id}/guidance/skills` | Skill catalog; optional `query` |
| `GET` | `/api/v1/projects/{project_id}/guidance/skills/{skill_id}` | Skill body by id |
| `POST` | `/api/v1/projects/{project_id}/guidance/skills:get` | Skill body by `skill_id` or `name` |
| `POST` | `/api/v1/projects/{project_id}/guidance/seed-mcp-first` | Idempotent MCP-first seed pack |
| `POST` | `/api/v1/projects/{project_id}/guidance/export` | Dry-run layout plan (`cursor` / `claude_compatible` / `generic_agents_md`) |

Design: `docs/15-agent-workspace-guidance/`.
