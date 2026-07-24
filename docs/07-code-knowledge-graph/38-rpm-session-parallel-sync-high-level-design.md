---
doc_id: ac.doc.ckg.rpm-session-parallel-sync-hld
title: 38 - RPM Session Parallel Sync High Level Design
doc_type: hld
status: active
schema_version: '1.0'
owner: code-graph-lead
summary: 'Runtime topology for RPM-session-gated parallel sync: file worker pool, LLM work
  queue, session registry, LockedStore (Postgres exclusive / Neo4j bounded), CLI/HTTP observe.'
tags:
- sync
- rpm
- hld
- llm-gateway
- code-graph
phase: 07-code-knowledge-graph
canonical_path: docs/07-code-knowledge-graph/38-rpm-session-parallel-sync-high-level-design.md
lifecycle_lane: current
concern_lane: design
audience_lane:
- platform-engineering
authority: informative
visibility: internal
linked_symbols:
- backend/packages/llm_gateway/gateway.py::LlmGateway
related_docs:
- ac.doc.ckg.rpm-session-parallel-sync-feature-spec
- ac.doc.ckg.rpm-session-parallel-sync-lld
- ac.doc.ckg.rpm-session-parallel-sync-risks
- ac.doc.ckg.sync-cpu-budget-and-store-concurrency-lld
- ac.doc.stack.litellm-llm-gateway
doc_version: 1.0.0
audience:
- engineer
- architect
primary_entities:
- RpmSessionGate
- SessionRegistry
- FileWorkerPool
- LockedStore
relations_declared:
- type: depends_on
  target: ac.doc.ckg.rpm-session-parallel-sync-feature-spec
- type: complements
  target: ac.doc.stack.litellm-llm-gateway
- type: complements
  target: ac.doc.ckg.sync-cpu-budget-and-store-concurrency-lld
chunk_hints:
  strategy: heading_h2
  max_tokens: 700
  overlap_tokens: 48
language: en
security_classification: internal
updated_at: '2026-07-24'
---

# 38 - RPM Session Parallel Sync High Level Design

## Implementation status

**Implemented.** Runtime matches this topology via `RpmSessionGate`,
`LockedStore` / bounded local embeddings, parallel `ingest_repo`, and session observe
surfaces (`GET /api/v1/llm/sessions`, `agentcore llm sessions`).

## Purpose

Show how `agentcore sync` parallelism, LiteLLM RPM sessions, and store writes
compose without exceeding RPM or corrupting persistence.

## Architecture overview

```mermaid
flowchart LR
  discover[DiscoverFiles] --> fileQueue[FileWorkerPool]
  fileQueue --> parseHash[ParseAndHash]
  parseHash --> llmQueue[LlmWorkQueue]
  llmQueue --> rpmGate[RpmSessionGate]
  rpmGate --> complete[gateway.complete_or_embed]
  complete --> writeQ[LockedStore_bounded]
  writeQ --> graph[(Postgres_or_Neo4j)]
  rpmGate --> registry[SessionRegistry_inMemory]
  registry --> observe[CLI_and_HTTP_status]
```

### Agent-readable primary flow

| Step | Component | Action | Output |
| --- | --- | --- | --- |
| 1 | CLI `cmd_sync` | Resolve roots + filters | Sync job params |
| 2 | `sync_repo` / discover | List eligible files | File list (capped) |
| 3 | FileWorkerPool | Parse + hash per file (bounded workers) | Changed symbols + pending writes |
| 4 | LlmWorkQueue | Enqueue doc/embed work needing LiteLLM | Work items with attribution |
| 5 | RpmSessionGate | Wait for RPM window + in-flight slot; start session | Session id |
| 6 | LiteLlmGateway | `complete` / `embed` | Text / vector or error |
| 7 | RpmSessionGate | End session in `finally` | Updated registry |
| 8 | LockedStore | Apply symbol/edge upserts (Postgres exclusive; Neo4j bounded) | Graph SoR update |
| 9 | Progress + observe | Emit progress; expose registry snapshot | CLI/HTTP status |

## Component ownership

| Component | Owns | Path (target) |
| --- | --- | --- |
| SessionRegistry + RpmSessionGate | Start/end, window, in-flight, snapshot | `backend/packages/llm_gateway/` (`rate_limit.py` evolution) |
| LiteLlmGateway | Call gate around every network complete/embed | `backend/packages/llm_gateway/gateway.py` |
| Parallel ingest scheduler | File workers, LLM queue, fairness | `code_graph_service/application/ingest/` |
| LockedStore | Postgres exclusive lock; Neo4j bounded Bolt slots | `code_graph_service/locked_store.py` |
| Progress tracker | Thread-safe progress events | `agentcore_cli/sync_progress/` |
| HTTP observe | Snapshot endpoint | `code_graph_service/api.py` (`/api/v1/llm/...`) |
| CLI observe | Status command / sync enrichment | `agentcore_cli` |

## Boundaries

```text
agentcore CLI
    │  sync / session status
    ▼
code-graph-service (in-process or HTTP)
    ├── Parallel ingest scheduler
    ├── LlmBackedDocGenerator / HybridEmbeddings  ──► llm_gateway
    │                                                      │
    │                                                      ├── RpmSessionGate
    │                                                      └── SessionRegistry
    └── LockedStore ──► Neo4jStore | PostgresStore
```

- **Domain ports** stay provider-agnostic; only the gateway opens RPM sessions.
- **Application ingest** may parallelize CPU work; it **must not** bypass the
  gateway for LiteLLM calls.
- **Registry** is process-local; two CLI processes have independent RPM truth.

## Parallelism policy (summary)

| Stage | Parallel? | Cap |
| --- | --- | --- |
| File parse + hash | Yes | auto `min(cpu, RPM)` or explicit `AGENTCORE_SYNC_MAX_FILE_WORKERS` |
| Local BGE embedding | Yes | four concurrent calls process-wide across cached models |
| LiteLLM calls | Yes | `AGENTCORE_LITELLM_RPM` + in-flight sessions |
| Store writes | No (v1) | Single writer thread / lock |

Embeddings via local BGE or stub skip the RPM gate. LiteLLM embeddings take a
session like completions.

## Observability surfaces

| Surface | Reads | Notes |
| --- | --- | --- |
| `GET /api/v1/llm/sessions` (exact path in LLD) | SessionRegistry snapshot | Loopback clients only; no secrets / prompts |
| CLI session status | Same snapshot | Reads an active CLI sync through its private (`0600`) transient progress snapshot; otherwise reads the running service via `AGENTCORE_CODE_GRAPH_URL` |
| Sync progress | File/symbol counters | Independent of session history ring |

The in-process CLI reads the secret-bearing code-graph service environment only
when its file is owned by the current user and has mode `0600`. A non-private LLM
route requires explicit per-run consent before ingest starts: interactive TTY
prompt (shows tenant, workspace, project, paths) or `--allow-cloud-llm`.

## Dependencies

- Existing ingest workflow: [`03`](03-ingestion-and-living-documentation-workflow.md)
- LiteLLM gateway ADR: [`09`](../13-technology-stack-and-platform-decisions/09-litellm-llm-gateway.md)
- Env reference: [`12`](../13-technology-stack-and-platform-decisions/12-litellm-environment-configuration.md)
- Feature requirements: [`37`](37-rpm-session-parallel-sync-feature-specification.md)

## Related Documents

- Feature spec: [`37`](37-rpm-session-parallel-sync-feature-specification.md)
- LLD: [`39`](39-rpm-session-parallel-sync-low-level-design.md)
- Risks: [`40`](40-rpm-session-parallel-sync-risks-challenges-and-acceptance.md)
