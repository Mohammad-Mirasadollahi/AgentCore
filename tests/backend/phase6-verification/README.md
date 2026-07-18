# Phase 6 Verification

Path: `tests/backend/phase6-verification`

## Purpose

Executable Phase 6 Technical Logic and Verification harness. This is not a product microservice. It checks Phases 1 through 5 for canonical paths, contracts, state machines, idempotency, redaction, and an in-process end-to-end runtime scenario before Phase 7 work.

## Layout

- Harness package: `tests/support/phase6/`
- Tests: `test_phase6.py`
- Gate CLI: `run_phase_gate.py`

## Run

```bash
PYTHONPATH=tests/support .venv/bin/python -m pytest tests/backend/phase6-verification
```

Full gate including Phase 1 through 5 suites:

```bash
.venv/bin/python tests/backend/phase6-verification/run_phase_gate.py --run-suites
```

Machine-readable report:

```bash
.venv/bin/python tests/backend/phase6-verification/run_phase_gate.py --json
```
