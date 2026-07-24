---
doc_id: ac.doc.adapter.phase-5-api-contract
title: Adapter Service Phase 5 API Contract
doc_type: contract
status: active
schema_version: '1.0'
owner: adapter-service
summary: This contract documents the Phase 5 interoperability vertical slice. The service
  owns scoped connectors, adapter mappings, Universal Agent JSON validation/normalization,
  in-service broker publish/subscribe/delivery/replay/dead-letter handling, external tickets,
  department work...
tags:
- adapter
- api
- contract
- phase-5
phase: phase-5
canonical_path: backend/services/adapter-service/docs/phase-5-api-contract.md
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

# Adapter Service Phase 5 API Contract

Path: `backend/services/adapter-service/docs/phase-5-api-contract.md`

## Purpose

This contract documents the Phase 5 interoperability vertical slice. The service owns scoped connectors, adapter mappings, Universal Agent JSON validation/normalization, in-service broker publish/subscribe/delivery/replay/dead-letter handling, external tickets, department workflow tasks, and adapter-service outbox events.

## Scope Headers

Every command and scoped query uses:

- `X-Tenant-Id`
- `X-Workspace-Id`
- `X-Actor-Id` for commands
- `X-Correlation-Id` when a caller needs deterministic trace linkage
- `Idempotency-Key` for retryable commands

All endpoints are scoped under `/api/v1/projects/{project_id}` and return snake_case JSON fields.

## Commands

- `POST /api/v1/projects/{project_id}/connectors`
- `POST /api/v1/projects/{project_id}/connectors/{connector_id}:validate`
- `POST /api/v1/projects/{project_id}/connectors/{connector_id}:rotate-credential`
- `POST /api/v1/projects/{project_id}/subscriptions`
- `POST /api/v1/projects/{project_id}/vendor-events:normalize`
- `POST /api/v1/projects/{project_id}/agent-events`
- `POST /api/v1/projects/{project_id}/broker:replay`
- `POST /api/v1/projects/{project_id}/external-tickets`
- `POST /api/v1/projects/{project_id}/external-tickets/{ticket_id}:sync-status`
- `POST /api/v1/projects/{project_id}/context:inject`

## Queries

- `GET /api/v1/projects/{project_id}/capabilities`
- `GET /api/v1/projects/{project_id}/connectors/{connector_id}/health`
- `GET /api/v1/projects/{project_id}/subscriptions`
- `GET /api/v1/projects/{project_id}/dead-letters`
- `GET /api/v1/projects/{project_id}/connectors/{connector_id}/mappings`
- `GET /api/v1/projects/{project_id}/department-tasks`

## Event Types

- `ConnectorRegistered`
- `ConnectorValidated`
- `CapabilityChanged`
- `AdapterNormalizedOutput`
- `AgentEventReceived`
- `BrokerEventPublished`
- `BrokerDeliveryFailed`
- `DeadLetterCreated`
- `IdeNotificationSent`
- `ExternalTicketCreated`
- `ExternalStatusSynced`
- `DepartmentTaskCreated`

## Compatibility

This is an active Phase 5 contract. A future split into standalone `broker-service` should preserve these message and subscription semantics.

## Related Documents

- `backend/docs/API_NAMING_AND_CONTRACT_STANDARD.md` — HTTP naming and contract conventions
- Sibling service design docs under `docs/` for the owning phase vertical slice
