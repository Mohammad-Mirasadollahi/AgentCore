# Backend Tests

Backend tests are grouped by owning service, phase gate, or package.

## Current suites

| Suite | Role |
|-------|------|
| `core-data-service/` | Phase 1 |
| `memory-service/` | Phase 2 |
| `docs-sync-service/` | Phase 3 |
| `rule-engine-service/` | Phase 4 |
| `adapter-service/` | Phase 5 |
| `phase6-verification/` | Phase 6 gate |
| `code-graph-service/` | Phase 7 |
| `phase8-verification/` | Phase 8 gate |
| `phase9-verification/` | Phase 9 gate |
| `phase10-verification/` | Phase 10 gate |
| `phase11-verification/` | Phase 11 gate |
| `packages/` | Shared package loaders |
| `audit-service/` | Platform audit slice |
| `identity-access-service/` | Platform identity slice |
| `orchestration-service/` | Platform orchestration slice |
| `reporting-service/` | Platform reporting slice |
| `project-profile-service/` | Platform project-profile slice |
| `common-context-service/` | Platform common-context slice |

Service-local `backend/**/tests/` directories are documentation-only placeholders. Canonical executable tests live here.

Use the project virtual environment and set `PYTHONPATH` to the service `src` (or `tests/support` / `backend/packages` for gates). Examples:

```bash
PYTHONPATH=backend/services/core-data-service/src .venv/bin/python -m pytest tests/backend/core-data-service -q
PYTHONPATH=tests/support:backend/packages .venv/bin/python -m pytest tests/backend/phase8-verification -q
```

Full command list: [../README.md](../README.md).
