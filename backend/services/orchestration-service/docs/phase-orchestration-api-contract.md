# AgentCore Orchestration API Contract

Vertical slice for `orchestration-service`.

- Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`
- Idempotency: `Idempotency-Key` on mutating routes
- Persistence target env: `AGENTCORE_ORCHESTRATION_DATABASE_URL`
- Tests: `tests/backend/services/orchestration-service/`
