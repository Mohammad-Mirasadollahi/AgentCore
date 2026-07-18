# AgentCore Common Context API Contract

Vertical slice for `common-context-service`.

- Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`
- Idempotency: `Idempotency-Key` on mutating routes
- Persistence target env: `AGENTCORE_COMMON_CONTEXT_DATABASE_URL`
- Tests: `tests/backend/common-context-service/`
