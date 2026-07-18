# AgentCore Project Profile API Contract

Vertical slice for `project-profile-service`.

- Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`
- Idempotency: `Idempotency-Key` on mutating routes
- Persistence target env: `AGENTCORE_PROJECT_PROFILE_DATABASE_URL`
- Tests: `tests/backend/project-profile-service/`
