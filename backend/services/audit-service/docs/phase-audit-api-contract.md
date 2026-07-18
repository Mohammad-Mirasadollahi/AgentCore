# AgentCore Audit API Contract

Vertical slice for `audit-service`.

- Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`
- Idempotency: `Idempotency-Key` on mutating routes
- Persistence target env: `AGENTCORE_AUDIT_DATABASE_URL`
- Tests: `tests/backend/audit-service/`
