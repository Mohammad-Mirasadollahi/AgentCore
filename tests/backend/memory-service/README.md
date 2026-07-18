# Memory Service Tests

Path: `tests/backend/memory-service`

## Purpose

Executable tests for the Phase 2 Memory and Context vertical slice.

## Scope

Tests cover scoped memory retrieval, consolidation, restricted memory boundaries, question normalization and FAQ promotion, WorkBatch readiness, idempotency, and outbox event contracts.

## Run

```bash
PYTHONPATH=backend/services/memory-service/src .venv/bin/python -m pytest tests/backend/memory-service
```
