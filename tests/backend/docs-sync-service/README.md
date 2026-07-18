# Docs Sync Service Tests

Path: `tests/backend/docs-sync-service`

## Purpose

Executable tests for the Phase 3 Docs-as-Code synchronization vertical slice.

## Scope

Tests cover frontmatter validation, symbol/document indexing, anchor registration, stale and missing drift detection, issue/task refs, Bloom negative lookup, CI gate fail/pass, draft approval, InMemoryStore scope/idempotency/not-found, HTTP API smoke for drift/CI/coverage, route registration, and outbox event contracts.

## Run

```bash
PYTHONPATH=backend/services/docs-sync-service/src .venv/bin/python -m pytest tests/backend/docs-sync-service
```
