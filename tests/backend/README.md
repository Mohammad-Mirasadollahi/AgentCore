# Backend Tests

Backend tests are grouped by owning service, app, or package.

Current suites:

- `core-data-service/` - Phase 1 Core Data Service tests.

Use the project virtual environment:

```bash
PYTHONPATH=backend/services/core-data-service/src .venv/bin/python -m pytest tests/backend
```

Service-local `backend/**/tests/` directories are documentation-only placeholders unless a future architecture decision changes the canonical test layout.
