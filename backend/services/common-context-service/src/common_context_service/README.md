# common_context_service (package map)

**Owns:** governed common items + Agent Workspace Guidance resolve/seed/export.

**Does not:** HTTP wiring (`api.py`), Postgres adapter (`postgres_store.py`), filesystem materialize details (`guidance_export.py`).

| Start here | Role |
| --- | --- |
| `service.py` | `CommonContextService` composition |
| `service_items.py` | propose / approve / suppress / reject / generic bundle |
| `service_guidance.py` | guidance resolve, list/get skill |
| `service_seed.py` | MCP-first seed pack |
| `service_export.py` | IDE layout export |
| `core.py` | backward-compatible re-exports |
| `ports.py` | `Store` protocol |
| `scope.py` / `errors.py` / `constants.py` / `util.py` | domain primitives |
