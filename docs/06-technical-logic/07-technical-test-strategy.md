# Technical Test Strategy

## Purpose

This document defines how to verify the technical logic of AgentCore. The platform should not be considered ready because documents exist. It is ready when the documented logic can be tested through deterministic, repeatable scenarios.

## Test Layers

### Contract Tests

Contract tests validate schemas and event shapes.

Required coverage:

- Activity schema.
- Decision schema.
- Issue and Task schema.
- MemoryItem and ContextBundle schema.
- Doc and CodeSymbol schema.
- Policy and RuleEvaluation schema.
- Universal Agent JSON schema.
- Broker event envelope.

### State Machine Tests

State machine tests validate legal transitions and reject illegal transitions.

Examples:

- Task cannot move from CREATED directly to VERIFIED.
- Decision cannot move from REJECTED to ACTIVE.
- Issue cannot close while required Tasks are incomplete.
- EscalationTicket cannot approve without an approver identity.

### Idempotency Tests

Idempotency tests replay the same input and verify no duplicate logical records are created.

Examples:

- Same agent message delivered twice.
- Same CI event replayed.
- Same docs drift finding reported twice.
- Same approval webhook retried.

### Redaction Tests

Redaction tests verify that sensitive data does not enter prompts, public events, or dashboards.

Examples:

- terminal output contains API key,
- diff contains password,
- external message contains customer data,
- artifact contains restricted log.

### Retrieval Tests

Retrieval tests verify that agents receive relevant current context.

Test cases:

- Current state is preferred over historical events.
- Deprecated facts are excluded by default.
- Restricted memory is denied to unauthorized agents.
- Relevant Decision is retrieved when linked code is touched.
- Token budget forces summarization with source references.

### Prompt Cache Tests

Prompt cache tests verify that static sections remain stable.

Test cases:

- Task-specific context does not invalidate static cache.
- Policy update invalidates static cache.
- Architecture Decision change invalidates static cache.
- Local command output does not invalidate static cache.

### Docs Drift Tests

Docs drift tests verify code/document synchronization.

Test cases:

- Public API body hash changes and linked doc is stale.
- Internal helper with `doc: n` changes and CI passes.
- Frontmatter references missing symbol and CI fails.
- Bloom filter negative result skips graph lookup.
- Bloom filter positive result is verified through graph.

### Rule Engine Tests

Rule tests verify deterministic and semantic policy behavior.

Test cases:

- Billing variable change triggers revenue policy.
- Authentication module change requires security approval.
- Low-risk refactor passes deterministic checks.
- LLM judge low confidence escalates.
- Conflicting policies require human review.

### Broker and Adapter Tests

Interoperability tests verify routing and delivery.

Test cases:

- Valid Universal Agent JSON is accepted.
- Invalid schema is rejected.
- Subscriber receives authorized event.
- Unauthorized subscriber is denied.
- Failed subscriber delivery creates dead-letter record.
- Replayed event does not duplicate Task state.

## End-to-End Test Scenario

Scenario: password hashing migration.

Expected flow:

1. Backend agent reports code changes.
2. Activities and WorkLog are created.
3. Decision is created for Argon2 choice.
4. Issue is discovered for old SHA256 hashes.
5. Tasks are generated for backend, data, QA, docs, and security.
6. Memory current state updates to Argon2.
7. Docs drift detector checks authentication docs.
8. Security policy requires approval.
9. Human approval is recorded.
10. Broker publishes completion events.
11. Future agent retrieves Argon2 Decision when touching auth code.

Pass criteria:

- Every entity has correlation ID.
- Every derived record has evidence references.
- No restricted evidence appears in prompt-visible context.
- High-risk security change is not allowed without approval.
- Docs sync status is updated.
- Broker events are replayable.

## Performance Tests

Required performance signals:

- Activity ingestion latency.
- Context retrieval latency.
- Prompt building latency.
- Bloom filter lookup latency.
- Rule evaluation latency.
- Broker delivery latency.
- LLM judge call count per workflow.

## Reliability Tests

Required reliability tests:

- replay same event stream from checkpoint,
- simulate broker subscriber outage,
- simulate vector store unavailable,
- simulate graph store timeout,
- simulate LLM provider failure,
- simulate approval webhook retry,
- simulate partial CI indexing failure.

## Technical Definition of Done

A phase is technically complete when:

- schemas are versioned,
- state transitions are tested,
- failure paths are documented,
- idempotency behavior is verified,
- audit reconstruction works,
- sensitive data is redacted,
- acceptance scenarios pass with evidence.

## Canonical Test Paths

AgentCore uses a root-level test tree. All executable tests must be discoverable from `tests/`.

```text
tests/frontend/                 frontend unit, component, integration, and e2e tests
tests/backend/                  backend unit, contract, integration, security, and live-gated tests
tests/backend/core-data-service/     Phase 1
tests/backend/memory-service/        Phase 2
tests/backend/docs-sync-service/     Phase 3
tests/backend/rule-engine-service/   Phase 4
tests/backend/adapter-service/       Phase 5
```

Phase documentation and module READMEs must reference these canonical paths. When a new service or app is implemented, create its executable tests under `tests/backend/<owner>/` or `tests/frontend/<owner>/` and keep service-local `tests/` folders empty or documentation-only.

Named validation commands for current Phase 1 through 5 slices:

```bash
PYTHONPATH=backend/services/core-data-service/src .venv/bin/python -m pytest tests/backend/core-data-service
PYTHONPATH=backend/services/memory-service/src .venv/bin/python -m pytest tests/backend/memory-service
PYTHONPATH=backend/services/docs-sync-service/src .venv/bin/python -m pytest tests/backend/docs-sync-service
PYTHONPATH=backend/services/rule-engine-service/src .venv/bin/python -m pytest tests/backend/rule-engine-service
PYTHONPATH=backend/services/adapter-service/src .venv/bin/python -m pytest tests/backend/adapter-service
```

Phase 6 harness and gate:

```bash
PYTHONPATH=tests/support .venv/bin/python -m pytest tests/backend/phase6-verification
.venv/bin/python tests/backend/phase6-verification/run_phase_gate.py
.venv/bin/python tests/backend/phase6-verification/run_phase_gate.py --run-suites
```

Harness package: `tests/support/phase6/`. A phase is not technically complete until its tests are in the canonical tree, its README names the exact command, and no executable test files remain hidden under source-owned service folders. Phase 6 is the roadmap gate that checks this completeness before Phase 7 implementation.

