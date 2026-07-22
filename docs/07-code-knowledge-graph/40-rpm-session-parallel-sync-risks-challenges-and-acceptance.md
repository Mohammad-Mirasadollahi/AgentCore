---
doc_id: ac.doc.ckg.rpm-session-parallel-sync-risks
title: 40 - RPM Session Parallel Sync Risks Challenges And Acceptance
doc_type: standard
status: draft
schema_version: '1.0'
owner: code-graph-lead
summary: Risks, challenges, known limits, and acceptance gates for RPM-session-tracked parallel
  sync.
tags:
- risks
- acceptance
- sync
- rpm
- concurrency
phase: 07-code-knowledge-graph
canonical_path: docs/07-code-knowledge-graph/40-rpm-session-parallel-sync-risks-challenges-and-acceptance.md
lifecycle_lane: current
concern_lane: problem
audience_lane:
- platform-engineering
- operators
authority: normative
visibility: internal
linked_symbols: []
related_docs:
- ac.doc.ckg.rpm-session-parallel-sync-feature-spec
- ac.doc.ckg.rpm-session-parallel-sync-lld
- ac.doc.stack.litellm-llm-gateway
doc_version: 1.0.0
audience:
- engineer
- architect
- operator
primary_entities:
- AcceptanceGate
- RpmSession
relations_declared:
- type: depends_on
  target: ac.doc.ckg.rpm-session-parallel-sync-feature-spec
chunk_hints:
  strategy: heading_h2
  max_tokens: 600
  overlap_tokens: 40
language: en
security_classification: internal
---

# 40 - RPM Session Parallel Sync Risks Challenges And Acceptance


## Purpose

Risks, challenges, known limits, and acceptance gates for RPM-session-tracked parallel sync. Designed ahead of implementation; gates unchecked until code.

## Implementation status

**Implemented.** Re-check acceptance gates below against the current tree when
claiming production readiness; keep multi-process RPM sharing as a known v1 limit.

Last verified: 2026-07-22

## Challenges (must be designed for)

| ID | Challenge | Why it bites | Design response |
| --- | --- | --- | --- |
| C-01 | Postgres single connection | `PostgresStore` holds one `psycopg` connection; concurrent cursors corrupt / error | v1 **SerializedStoreWriter** (single writer / lock) |
| C-02 | RPM starts ≠ in-flight | Long completions keep provider busy after “start” counted | Dual gate: sliding starts **and** in-flight cap |
| C-03 | Session leaks | Exception / timeout without `finally` leaves ghost in-flight | Mandatory `release` in `finally`; unit leak tests |
| C-04 | Idempotency races | Parallel `ingest_file` sharing keys or overlapping completes | Unique per-file keys; begin/complete under writer lock |
| C-05 | Cross-file edges | Waiting for peer files deadlocks; ignoring peers drops edges | No cross-file wait; unresolved calls/imports/inheritance relink as peer symbols land |
| C-06 | Retry accounting | SDK `num_retries` multiplies provider load | One outer session per gateway invocation (LLD); document load effect |
| C-07 | Heuristic / stub false RPM | Runtime fallback must not acquire or leave sessions | No `acquire` on runtime heuristic/local-stub paths; `FakeLlmGateway` explicitly emulates network-session semantics in tests |
| C-08 | Local BGE vs LiteLLM embed | BGE must not consume RPM slots or serialize all files | Only `gateway.embed` acquires; model construction is process-serialized and inference is bounded to four concurrent calls process-wide across cached models |
| C-09 | Hung sessions | Provider hang beyond operator patience | Timeout = `AGENTCORE_LITELLM_TIMEOUT_SECONDS`; forced end |
| C-10 | Multi-process CLI | Two `agentcore sync` processes do not share registry | Document known limit; no Redis in v1 |
| C-11 | File monopoly | One huge file’s symbols starve others | Per-file round-robin DocWork scheduling |
| C-12 | Progress races | Unsynchronized counters mislead ETA | Lock/queue in `SyncProgressTracker` |
| C-13 | Observability secrets | Status API could leak prompts/keys | Snapshot fields allowlist only |
| C-14 | Test flakiness | Real 60s sleeps | Fake clock / injected time; never sleep a full minute in unit CI |
| C-15 | CLI/service config drift | In-process sync silently falls back when model env is absent | Graph CLI loads repo-root `.env` (single source of truth); process env retains precedence |
| C-16 | Silent cloud code egress | A configured provider may receive symbol bodies without per-run consent | Non-private/uncertain routes fail closed before ingest; interactive TTY consent (tenant/workspace/project/paths shown) or `--allow-cloud-llm` |

## Risks

| ID | Risk | Mitigation |
| --- | --- | --- |
| R-01 | Operators believe RPM is cluster-wide | Docs + CLI banner: process-local; warn if multiple syncs |
| R-02 | Raising file workers without RPM headroom | Queue grows; wall time flat; document worker ≤ inflight guidance |
| R-03 | Serial writer becomes bottleneck after LLM | Acceptable in v1; follow-up = connection pool + careful Neo4j concurrency |
| R-04 | Provider 429 despite client RPM | Lower RPM; retries amplify load — tune `NUM_RETRIES` |
| R-05 | Partial graph on soft-fail | Same as today; outcomes list failed files |
| R-06 | Docs claim shipped while code serial | `lifecycle_lane: current` until gates pass; honesty in status section |

## Known limits (v1)

- Session registry and RPM truth are **per process**.
- History is **short** (100) and **volatile** (lost on exit).
- Human-docs Phase 2 may remain serial.
- No distributed limiter across hosts.

## Acceptance gates

Uncheck → check only when proven in code + tests.

### Session gate

- [x] Every LiteLLM `complete`/`embed` has matching start and end (no leak tests).
- [x] Concurrent threads never observe `starts_in_window > rpm` or `inflight > cap`.
- [x] Timeout path ends the session; registry count drops.
- [x] Heuristic / local BGE / stub paths create **zero** sessions.

### Parallel sync gate

- [x] File parse/hash runs with bounded workers (`AGENTCORE_SYNC_MAX_FILE_WORKERS`).
- [x] Store mutations serialized; Neo4j and single-connection Postgres paths pass
  `test_rpm_session_parallel_sync_live.py` with concurrent local HTTP LLM calls.
- [x] Production composition with real cached BGE, real Neo4j, five changed files,
  and local HTTP reaches `http_peak=5` and `rpm_peak=5`
  (`test_production_build_sends_five_files_concurrently`).
- [x] Multiple service instances and cached models observe the same four-call
  process-wide bound
  (`test_local_embedding_limit_is_shared_across_service_instances`).
- [x] Concurrent cache misses cannot construct multiple large local models at once
  (`test_local_model_loads_are_process_serialized`).
- [x] Per-file soft-fail preserved; one failure does not abort the job.
- [ ] Fairness: multi-file fixture shows interleaved DocWork under low inflight cap.
- [x] Idempotency keys unique per file under concurrency.

### Observability gate

- [x] `GET /api/v1/llm/sessions` (or final path) returns inflight + history + RPM stats.
- [x] CLI exposes the same snapshot fields from an active CLI sync or the running
  HTTP service (`test_llm_sessions_prefers_active_sync_process`,
  `test_llm_sessions_reads_running_service_snapshot`; live HTTP/CLI verified 2026-07-22).
- [x] Live CLI progress observes non-zero concurrent sessions instead of only
  configured capacity (`test_cli_progress_reports_nonzero_live_rpm`).
- [x] CLI loads LiteLLM / model configuration from repo-root `.env`
  (`test_load_dotenv_files_reads_root_litellm_config`,
  `test_graph_cli_builds_gateway_from_root_env`).
- [x] Cloud/uncertain LLM routes require explicit per-run consent before sync,
  graph explore, or hybrid search — interactive TTY (tenant/workspace/project/paths)
  or `--allow-cloud-llm` (`test_sync_cloud_llm_requires_explicit_per_run_consent`,
  `test_cloud_llm_consent_prompt_shows_scope_and_path`,
  `test_graph_query_commands_apply_cloud_consent_guard`).
- [x] Payloads contain no API keys, prompts, completion bodies, or raw provider
  error text (`test_litellm_gateway_releases_sessions_on_failures`).
- [x] Detailed HTTP sessions are loopback-only, and the transient CLI snapshot
  is explicitly `0600` (`test_llm_sessions_route_is_loopback_only`,
  `test_tracker_snapshot_is_private_before_json_is_written`).
- [x] Sync progress remains coherent under parallel workers.
- [x] Unchanged session polls do not rewrite/fsync transient progress
  (`test_tracker_skips_unchanged_session_snapshot`).

### Documentation / honesty gate

- [x] Pack `37`–`40` field names match implementation.
- [x] `lifecycle_lane` moved from `future` to `current` only after gates above.
- [x] LiteLLM env doc (`12`) updated for session/in-flight semantics and new knobs.
- [x] Ingest workflow (`03`) notes parallel pipeline + serial writer.

## Open gaps (post-v1)

| Gap | Notes |
| --- | --- |
| Postgres connection pool | Enables safer parallel writers; separate design |
| Shared limiter across processes | Redis/file lock — only if multi-sync becomes common |
| Attempt-level session nesting | If ops need per-retry visibility |
| Parallel human-docs Phase 2 | After code ingest path is proven |

## Related Documents

- Feature: [`37`](37-rpm-session-parallel-sync-feature-specification.md)
- HLD: [`38`](38-rpm-session-parallel-sync-high-level-design.md)
- LLD: [`39`](39-rpm-session-parallel-sync-low-level-design.md)
- LiteLLM ADR: [`09`](../13-technology-stack-and-platform-decisions/09-litellm-llm-gateway.md)
