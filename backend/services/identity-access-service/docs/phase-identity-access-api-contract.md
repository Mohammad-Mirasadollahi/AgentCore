# AgentCore Identity Access API Contract

Vertical slice for `identity-access-service`.

- Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`
- Idempotency: `Idempotency-Key` on mutating routes
- Persistence target env: `AGENTCORE_IDENTITY_ACCESS_DATABASE_URL`
- Tests: `tests/backend/services/identity-access-service/`
