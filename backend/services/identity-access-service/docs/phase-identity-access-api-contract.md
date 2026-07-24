---
doc_id: ac.doc.identity-access.phase-identity-access-api-contract
title: AgentCore Identity Access API Contract
doc_type: contract
status: active
schema_version: '1.0'
owner: identity-access-service
summary: 'Vertical slice for `identity-access-service`. Vertical slice for `identity-access-service`.
  - Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id` - Idempotency: `Idempotency-Key`
  on mutating routes - Persistence target env: `AGENTCORE_IDENTITY_ACCESS_DATABASE_URL` -
  T...'
tags:
- api
- contract
- identity-access
- phase-identity-access
phase: phase-identity-access
canonical_path: backend/services/identity-access-service/docs/phase-identity-access-api-contract.md
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

# AgentCore Identity Access API Contract


## Purpose

Vertical slice for `identity-access-service`.

Vertical slice for `identity-access-service`.

- Scope headers: `X-Tenant-Id`, `X-Workspace-Id`, `X-Actor-Id`
- Idempotency: `Idempotency-Key` on mutating routes
- Persistence target env: `AGENTCORE_IDENTITY_ACCESS_DATABASE_URL`
- Tests: `tests/backend/services/identity-access-service/`

## Related Documents

- `backend/docs/API_NAMING_AND_CONTRACT_STANDARD.md` — HTTP naming and contract conventions
- Sibling service design docs under `docs/` for the owning phase vertical slice
