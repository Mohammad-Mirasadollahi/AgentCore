# Outbox Relay

Path: `backend/packages/outbox_relay` · Worker: `backend/apps/worker`

## Purpose

Transactional outbox relay for AgentCore. Polls unpublished rows from every service `*.outbox` table, runs platform handlers, then marks rows with `published_at`.

## Handlers

| Handler | Trigger | Effect |
|---------|---------|--------|
| `memory_from_core_data` | `core-data` create/activity events | Candidate semantic memory |
| `audit_mirror` | every event | Immutable audit record |
| `broker_forward` | selected `core-data` events | Adapter broker publish |

## Outbox DDL shapes

| Shape | Services | Mark key |
|-------|----------|----------|
| `event_id` + `event_type` + payload | core-data, memory, docs-sync, code-graph, rule-engine, adapter | `event_id` |
| `seq` + payload | audit, identity-access, orchestration, reporting, project-profile, common-context | `seq` |

`code-graph` uses `created_at` instead of `occurred_at`. The relay normalizes both families.

## Run

```bash
export AGENTCORE_DATABASE_URL=postgresql://agentcore:secret@127.0.0.1:32232/agentcore
PYTHONPATH=backend/packages:backend/apps/worker/src:backend/services/memory-service/src:backend/services/audit-service/src:backend/services/adapter-service/src \
  .venv/bin/python -m agentcore_worker --once --json
```

Poll forever (default):

```bash
PYTHONPATH=backend/packages:backend/apps/worker/src:backend/services/memory-service/src:backend/services/audit-service/src:backend/services/adapter-service/src \
  .venv/bin/python -m agentcore_worker
```

Compose profile `all` includes `outbox-relay` beside Postgres.

## Env

| Variable | Purpose |
|----------|---------|
| `AGENTCORE_DATABASE_URL` | Required PostgreSQL URL |
| `AGENTCORE_OUTBOX_SOURCES` | Optional comma list of source names |
| `AGENTCORE_OUTBOX_BATCH_SIZE` | Default 100 |
| `AGENTCORE_OUTBOX_POLL_INTERVAL` | Seconds between polls (default 2) |
| `AGENTCORE_OUTBOX_MEMORY_HANDLER` | `true`/`false` |
| `AGENTCORE_OUTBOX_AUDIT_HANDLER` | `true`/`false` |
| `AGENTCORE_OUTBOX_BROKER_HANDLER` | `true`/`false` |

## Tests

```bash
PYTHONPATH=backend/packages:backend/services/memory-service/src:backend/services/audit-service/src:backend/services/adapter-service/src:backend/services/core-data-service/src \
  .venv/bin/python -m pytest tests/backend/tools/outbox-relay -q
```

## Status

Implemented. In-memory source for unit tests; PostgreSQL source for runtime.
