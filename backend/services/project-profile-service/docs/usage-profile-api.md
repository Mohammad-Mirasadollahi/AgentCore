# Usage Profile API (project-profile-service)

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/usage-profiles` | List catalog profile ids |
| POST | `/api/v1/projects/{project_id}/usage-profile:activate` | Activate a Usage Profile on the project |
| GET | `/api/v1/projects/{project_id}/usage-profile/effective` | Resolve effective profile for scope |
| GET | `/api/v1/projects/{project_id}/usage-profile/cursor-mcp` | Materialize Cursor `mcpServers` fragment |

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
