# Code Graph Service Phase 7 API Contract

Path: `backend/services/code-graph-service/docs/phase-7-api-contract.md`

## Purpose

This contract documents the Phase 7 vertical slice for the Code-Knowledge Graph. The service owns scoped graph symbol projections, relationship edges (CONTAINS, CALLS, IMPORTS, INHERITS_FROM), hash-based change detection, local documentation generation for changed symbols only, semantic ranking, generation-context packs, generated-code symbol validation, and code-graph outbox events.

Neo4j remains the target structural store in the product design. This Phase 7 slice persists a graph projection in PostgreSQL (`code_graph` schema) and uses an in-memory Store fake for unit tests. Documentation generation is local and deterministic (no cloud model calls).

## Scope Headers

Every command and scoped query uses:

- `X-Tenant-Id`
- `X-Workspace-Id`
- `X-Actor-Id` for commands
- `X-Correlation-Id` when a caller needs deterministic trace linkage
- `Idempotency-Key` for retryable ingest commands

All endpoints are scoped under `/api/v1/projects/{project_id}` and return snake_case JSON fields.

## Commands

- `POST /api/v1/projects/{project_id}/graph/ingest-file`
- `POST /api/v1/projects/{project_id}/graph/search:semantic`
- `POST /api/v1/projects/{project_id}/graph/generation-context`
- `POST /api/v1/projects/{project_id}/graph/generated-code:validate`

## Queries

- `GET /api/v1/projects/{project_id}/graph/symbols/{symbol_id}`
- `GET /api/v1/projects/{project_id}/graph/symbols/{symbol_id}/neighbors`

## Event Types

The development outbox emits versioned code-graph-service events:

- `FileIngested`
- `SymbolsDocumented`

Each event contains `event_id`, `event_type`, `event_version`, `occurred_at`, `producer`, scope fields, `actor_ref`, `correlation_id`, `causation_id`, `idempotency_key`, `payload`, and `evidence_refs`.

## Compatibility

This is an active Phase 7 contract. Breaking changes require a new contract note, matching tests, and a migration or compatibility statement before promotion to shared contracts.
