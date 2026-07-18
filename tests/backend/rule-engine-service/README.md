# Rule Engine Service Tests

Path: `tests/backend/rule-engine-service`

## Purpose

Executable tests for the Phase 4 Rule Engine and Orchestration vertical slice.

## Scope

Tests cover sensitive-action blocking with approval (security/revenue/compliance), LLM/heuristic verdict rationale and evidence, API/schema impact task routing with idempotent replay, shadow mode, feedback, InMemoryStore scope/idempotency/not-found, HTTP API smoke for evaluate/approval/health, route registration, and outbox event contracts.

## Run

```bash
PYTHONPATH=backend/services/rule-engine-service/src .venv/bin/python -m pytest tests/backend/rule-engine-service
```
