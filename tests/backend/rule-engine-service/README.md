# Rule Engine Service Tests

Path: `tests/backend/rule-engine-service`

## Purpose

Executable tests for the Phase 4 Rule Engine and Orchestration vertical slice.

## Scope

Tests cover sensitive-action blocking with approval, LLM/heuristic verdict rationale and evidence, API/schema impact task routing, shadow mode, feedback, scope isolation, and outbox event contracts.

## Run

```bash
PYTHONPATH=backend/services/rule-engine-service/src .venv/bin/python -m pytest tests/backend/rule-engine-service
```
