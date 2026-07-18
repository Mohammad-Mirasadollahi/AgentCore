# Adapter Service Tests

Path: `tests/backend/adapter-service`

## Purpose

Executable tests for the Phase 5 interoperability vertical slice.

## Scope

Tests cover two-vendor task-state exchange through Universal Agent JSON, IDE broker delivery, dead-letter visibility, replay, and code-release department workflow tasks.

## Run

```bash
PYTHONPATH=backend/services/adapter-service/src .venv/bin/python -m pytest tests/backend/adapter-service
```
