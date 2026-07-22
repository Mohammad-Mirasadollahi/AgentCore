# AgentCore Common Context API Contract

Vertical slice for `common-context-service`.

- Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`
- Idempotency: `Idempotency-Key` on mutating propose routes
- Persistence target env: `AGENTCORE_COMMON_CONTEXT_DATABASE_URL`
- Tests: `tests/backend/services/common-context-service/`

## Guidance layers (`scope_kind`)

| Kind | Storage `project_id` | Who | Allowed item types |
| --- | --- | --- | --- |
| `project` (default) | Path `{project_id}` | Project admin | `general`, `agents_entry`, `always_rule`, `skill` |
| `org` | `__org__` | Org operator | same as project |
| `user` | `__user__:{user_id}` | Developer (own actor) | `skill`, non-mandatory `always_rule` only |

Propose body may set `scope_kind` and optional `user_id` (defaults to `X-Actor-Id` for user layer).

Resolve / list / get-skill merge **org + project + user** (when actor/`user_id` present). Precedence: task > user > project > org. Mandatory lower-layer items block conflicting higher-layer replacements (`mandatory_override_blocked`).

## Common items

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/projects/{project_id}/common-items` | Propose; optional `item_type`, `scope_kind`, `user_id` |
| `POST` | `/api/v1/projects/{project_id}/common-items/{item_id}:approve` | Approve; one `agents_entry` / unique skill `name` **per layer scope** |
| `POST` | `/api/v1/projects/{project_id}/common-items/{item_id}:suppress` | Suppress |
| `POST` | `/api/v1/projects/{project_id}/common-items/{item_id}:reject` | Reject |
| `GET` | `/api/v1/projects/{project_id}/common-context/bundle` | Generic score/budget resolve (project layer only) |

## Agent Workspace Guidance

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/projects/{project_id}/guidance/resolve` | Merged AWG bundle; uses `X-Actor-Id` as user layer; optional body `user_id`, `task_overrides` |
| `GET` | `/api/v1/projects/{project_id}/guidance/skills` | Merged skill catalog; optional `query` |
| `GET` | `/api/v1/projects/{project_id}/guidance/skills/{skill_id}` | Skill body by id (any considered layer) |
| `POST` | `/api/v1/projects/{project_id}/guidance/skills:get` | Skill body by `skill_id` or `name` |
| `POST` | `/api/v1/projects/{project_id}/guidance/seed-mcp-first` | Idempotent MCP-first seed (project layer) |
| `POST` | `/api/v1/projects/{project_id}/guidance/export` | Dry-run layout plan (`cursor` / `claude_compatible` / `generic_agents_md`) |

Design: `docs/15-agent-workspace-guidance/`.
