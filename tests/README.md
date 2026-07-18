# Tests

All executable tests live under this directory.

## Layout

```text
tests/
  support/                 Phase gate harnesses (phase6, phase8–phase11)
  backend/                 Backend pytest suites by service / phase gate
  frontend/                Frontend suites
  e2e/                     End-to-end harnesses (legacy Change Society under change-society/)
  live/                    Live / remote suites (legacy Change Society under change-society/)
```

Do not add executable tests under service-local source folders such as `backend/services/<service>/tests/`. Keep tests grouped here by owner so local commands and CI discovery stay predictable.

## Backend — phase slices

```bash
PYTHONPATH=backend/services/core-data-service/src .venv/bin/python -m pytest tests/backend/core-data-service -q
PYTHONPATH=backend/services/memory-service/src .venv/bin/python -m pytest tests/backend/memory-service -q
PYTHONPATH=backend/services/docs-sync-service/src .venv/bin/python -m pytest tests/backend/docs-sync-service -q
PYTHONPATH=backend/services/rule-engine-service/src .venv/bin/python -m pytest tests/backend/rule-engine-service -q
PYTHONPATH=backend/services/adapter-service/src .venv/bin/python -m pytest tests/backend/adapter-service -q
PYTHONPATH=backend/services/code-graph-service/src .venv/bin/python -m pytest tests/backend/code-graph-service -q
```

## Backend — phase gates

```bash
PYTHONPATH=tests/support .venv/bin/python -m pytest tests/backend/phase6-verification -q
PYTHONPATH=tests/support:backend/packages .venv/bin/python -m pytest tests/backend/phase8-verification -q
PYTHONPATH=tests/support:backend/packages .venv/bin/python -m pytest tests/backend/phase9-verification -q
PYTHONPATH=tests/support:backend/packages .venv/bin/python -m pytest tests/backend/phase10-verification -q
PYTHONPATH=tests/support:backend/packages .venv/bin/python -m pytest tests/backend/phase11-verification -q
```

## Backend — shared packages and platform services

```bash
PYTHONPATH=backend/packages .venv/bin/python -m pytest tests/backend/packages -q

PYTHONPATH=backend/services/audit-service/src .venv/bin/python -m pytest tests/backend/audit-service -q
PYTHONPATH=backend/services/identity-access-service/src .venv/bin/python -m pytest tests/backend/identity-access-service -q
PYTHONPATH=backend/services/orchestration-service/src .venv/bin/python -m pytest tests/backend/orchestration-service -q
PYTHONPATH=backend/services/reporting-service/src .venv/bin/python -m pytest tests/backend/reporting-service -q
PYTHONPATH=backend/services/project-profile-service/src .venv/bin/python -m pytest tests/backend/project-profile-service -q
PYTHONPATH=backend/services/common-context-service/src .venv/bin/python -m pytest tests/backend/common-context-service -q
```

See also [tests/backend/README.md](backend/README.md) and [docs/06-technical-logic/07-technical-test-strategy.md](../docs/06-technical-logic/07-technical-test-strategy.md).

## Frontend

Frontend tests belong under `tests/frontend/`.

## Legacy Change Society

Archived demo assets live under `archives/hackathon/`. Historical suites may remain under `tests/backend/change-society-service/`, `tests/e2e/change-society/`, and `tests/live/change-society/` for reference; they are not the primary AgentCore platform path.
