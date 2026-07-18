# Tests

All executable tests live under this directory.

## Layout

```text
tests/
  support/           pack-bootstrap.sh, hackathon_pack.py (resolve hackathon pack from monorepo)
  frontend/          frontend unit tests + tests/frontend/change-society/run-frontend-tests.sh
  backend/           backend pytest suites + tests/backend/change-society-service/run-pytest.sh, tests/backend/change-society-service/run-integrator-unit-tests.sh
  e2e/change-society/ deterministic society harness, integrator e2e, evaluation evidence
  live/change-society/ live Qwen, remote verify, integrator live suites
```

Do not add executable tests under service-local source folders such as `backend/services/<service>/tests/`. Keep tests grouped here by owner so local commands and CI discovery stay predictable.

Test **runners** (shell/Python harness) live next to each suite under `tests/backend/`, `tests/frontend/`, `tests/e2e/change-society/`, and `tests/live/change-society/`. **`hackathon/scripts/`** is install/ops only.

## Backend

Run backend tests with the AgentCore virtual environment. Example for Phase 1 Core Data Service:

```bash
PYTHONPATH=backend/services/core-data-service/src .venv/bin/python -m pytest tests/backend/core-data-service
```

Phase 6 verification gate (paths, contracts, runtime stitch of Phases 1 through 5):

```bash
PYTHONPATH=tests/support .venv/bin/python -m pytest tests/backend/phase6-verification
.venv/bin/python tests/backend/phase6-verification/run_phase_gate.py
```

Change Society (hackathon):

```bash
bash tests/backend/change-society-service/run-pytest.sh -q
```

Run all backend tests:

```bash
PYTHONPATH=backend/services/core-data-service/src .venv/bin/python -m pytest tests/backend
```

## Frontend

Frontend tests belong under `tests/frontend/`. Change Society:

```bash
bash tests/frontend/change-society/run-frontend-tests.sh
```

## E2E and live harness

| Kind | Directory | Example |
| --- | --- | --- |
| Deterministic society proof | `tests/e2e/change-society/` | `tests/e2e/change-society/run-real-test-suite.sh` |
| Live Qwen / remote API | `tests/live/change-society/` | `tests/live/change-society/run-live-test.sh remote` |
