---
doc_id: ac.doc.orchestration.phase-orchestration-api-contract
title: AgentCore Orchestration API Contract
doc_type: contract
status: active
schema_version: '1.0'
owner: orchestration-service
summary: 'Vertical slice for `orchestration-service`. Vertical slice for `orchestration-service`.
  - Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id` - Idempotency: `Idempotency-Key`
  on mutating routes - Persistence target env: `AGENTCORE_ORCHESTRATION_DATABASE_URL` - Tests:...'
tags:
- api
- contract
- orchestration
- phase-orchestration
phase: phase-orchestration
canonical_path: backend/services/orchestration-service/docs/phase-orchestration-api-contract.md
lifecycle_lane: current
concern_lane: contract
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
doc_version: 1.0.0
updated_at: '2026-07-24'
linked_symbols: []
---

# AgentCore Orchestration API Contract


## Purpose

Vertical slice for `orchestration-service`.

Vertical slice for `orchestration-service`.

- Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`
- Idempotency: `Idempotency-Key` on mutating routes
- Persistence target env: `AGENTCORE_ORCHESTRATION_DATABASE_URL`
- Tests: `tests/backend/services/orchestration-service/`

## Related Documents

- `backend/docs/API_NAMING_AND_CONTRACT_STANDARD.md` — HTTP naming and contract conventions
- Sibling service design docs under `docs/` for the owning phase vertical slice
