# AgentCore Reporting API Contract

Vertical slice for `reporting-service`.

- Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`
- Idempotency: `Idempotency-Key` on mutating routes
- Persistence target env: `AGENTCORE_REPORTING_DATABASE_URL`
- Tests: `tests/backend/reporting-service/`
