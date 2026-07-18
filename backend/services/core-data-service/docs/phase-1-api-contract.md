# Phase 1 API Contract

Version: 1.0.0

All commands require `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`, and `Idempotency-Key`. Requests and responses use snake_case and project scope is enforced before reads or writes.

## Resources

- `POST /api/v1/projects/{project_id}/activities`
- `GET /api/v1/projects/{project_id}/activities`
- `POST /api/v1/projects/{project_id}/work-logs`
- `GET /api/v1/projects/{project_id}/work-logs`
- `POST /api/v1/projects/{project_id}/decisions`
- `GET /api/v1/projects/{project_id}/decisions`
- `POST /api/v1/projects/{project_id}/decisions/{decision_id}:supersede`
- `POST /api/v1/projects/{project_id}/issues`
- `GET /api/v1/projects/{project_id}/issues`
- `GET /api/v1/projects/{project_id}/open-issues`
- `POST /api/v1/projects/{project_id}/tasks`
- `GET /api/v1/projects/{project_id}/tasks`
- `POST /api/v1/projects/{project_id}/tasks/{task_id}:transition`
- `GET /api/v1/projects/{project_id}/task-board`
- `GET /api/v1/projects/{project_id}/decision-history`
- `GET /api/v1/projects/{project_id}/related-work`
- `GET /api/v1/projects/{project_id}/evidence-bundles/{evidence_ref}`
- `GET /api/v1/projects/{project_id}/timeline`

List calls require bounded `page_size` where exposed and return items, page metadata, and correlation data. Expected failures use the API problem envelope. Every mutation emits a versioned outbox event with scope, actor, correlation, causation, idempotency metadata, source, and evidence references.

Critical Issues must include `task_specs` for decomposition or `escalation_reason` for documented human escalation. Decision supersession keeps the old Decision record and moves it to `superseded` rather than deleting it.

PostgreSQL is the only runtime and integration persistence backend and is configured through `AGENTCORE_CORE_DATA_DATABASE_URL`. Deterministic unit tests use the Store port's in-memory fake.
