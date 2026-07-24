---
doc_id: ac.doc.ckg.index
title: 07 - Code-Knowledge Graph Index
doc_type: index
status: active
schema_version: '1.0'
owner: platform-docs
summary: 'This section adds the Code-Knowledge Graph design to AgentCore. The graph is the
  core wedge mechanism: connect a repository, understand it as structured knowledge, and improve
  connected AI coding outputs through task-scoped context packs.'
tags:
- index
- ckg
phase: 07-code-knowledge-graph
canonical_path: docs/07-code-knowledge-graph/00-index.md
lifecycle_lane: current
concern_lane: onboarding
audience_lane:
- platform-engineering
- agents
authority: informative
visibility: internal
linked_symbols:
- tests/backend/services/code-graph-service/test_code_graph_service.py::check_password
doc_version: 1.0.0
updated_at: '2026-07-24'
---

# 07 - Code-Knowledge Graph Index

## Purpose

This section adds the Code-Knowledge Graph design to AgentCore. The graph is the core wedge mechanism: connect a repository, understand it as structured knowledge, and improve connected AI coding outputs through task-scoped context packs.

This design extends the existing Docs-as-Code and Technical Logic sections. It focuses specifically on graph-backed code understanding, live documentation generation, and graph-guided code generation. Product positioning lives in `../00-master-plan/01-product-scope-and-feature-catalog.md`.

## Files

- `01-vision-and-scope.md` defines the purpose, positioning, and expected benefits of the Code-Knowledge Graph.
- `02-neo4j-schema-design.md` defines graph nodes, relationships, properties, constraints, and indexing strategy.
- `03-ingestion-and-living-documentation-workflow.md` defines explicit ingest (commit/PR/manual/CI), parsing, hashing, documentation, and graph upsert — not save-triggered continuous indexing.
- `04-graph-guided-code-generation-workflow.md` defines how AI code generation retrieves context from the graph instead of reading the whole repository.
- `05-token-optimization-and-model-routing.md` defines hash-based diffing, smart triggers, tiered LLM routing via LiteLLM, hierarchical summaries, and cheap embeddings.
- `06-technical-implementation-logic.md` defines implementation-level algorithms, pseudo-code, failure handling, and integration points.
- `07-metadata-first-code-understanding.md` defines the metadata-first architecture that lets agents inspect compact code metadata before reading source code.
- `08-code-metadata-schema-and-lifecycle.md` defines low-level metadata records, lifecycle, freshness states, confidence rules, and source escalation policy.
- `09-context-pack-retrieval-and-agent-workflow.md` defines context packs, retrieval algorithms, agent workflows, use cases, metrics, and safety rules.
- `10-language-support-policy.md` defines mandatory Python support and the planned language matrix.
- `11-neo4j-migration-plan.md` defines Postgres → Neo4j cutover steps without regressing Python.
- `12-neo4j-runtime-plugins.md` defines required APOC and Graph Data Science plugins for Neo4j.
- `13-codesymbol-projection-adr.md` accepts `CodeSymbol` + `CODE_REL` as the canonical Neo4j runtime projection.
- `14-repository-code-wiki-feature-specification.md` defines Repository Code Wiki (holistic repo-level wiki generation; CodeWiki / Google Code Wiki–inspired).
- `15-repository-code-wiki-high-level-design.md` defines wiki job architecture, ownership, and boundaries with living docs and docs-sync.
- `16-repository-code-wiki-low-level-design.md` defines module-tree, hierarchical decomposition, incremental dirty-set, and Mermaid validation algorithms.
- `17-repository-code-wiki-data-contracts-and-events.md` defines job/page/MCP contracts and domain events.
- `18-repository-code-wiki-risks-challenges-and-acceptance.md` defines risks, acceptance gates, and open gaps.
- `19-competitive-code-intelligence-roadmap-adr.md` adopts Wave 1–3 roadmap from CodeGraph / code-review-graph / graphify (explore, risk, routes, communities) without SQLite SoR.
- `20-repository-code-wiki-prior-art-ideas-and-license.md` catalogs transferable CodeWiki / Google Code Wiki ideas and normative license rules.
- `21-code-intelligence-prior-art-ideas-and-license.md` catalogs transferable CodeGraph / code-review-graph / graphify ideas and **MIT** compliance rules.
- `THIRD_PARTY_NOTICES.md` retains MIT copyright and permission notices for those three projects.
- `22-code-intelligence-enhancements-feature-specification.md` product requirements for explore, routes, TESTED_BY, change risk, Wave 2–3 analytics.
- `23-code-intelligence-enhancements-high-level-design.md` runtime topology and module boundaries.
- `24-code-intelligence-enhancements-low-level-design.md` algorithms (routes, flows, risk, explore, Leiden/RRF sketches).
- `25-code-intelligence-enhancements-data-contracts-and-events.md` HTTP/MCP payloads and edge metadata.
- `26-code-intelligence-enhancements-risks-challenges-and-acceptance.md` risks, license pitfalls, acceptance gates.
- `27-production-retrieval-stack-feature-specification.md` BM25 + store FTS + BGE + APOC + free Leiden requirements.
- `28-production-retrieval-stack-high-level-design.md` retrieval topology and module ownership.
- `29-production-retrieval-stack-low-level-design.md` BM25/RRF/FTS/APOC/Leiden algorithms.
- `30-production-retrieval-stack-data-contracts-and-events.md` hybrid/path/architecture transparency fields.
- `31-production-retrieval-stack-risks-challenges-and-acceptance.md` risks and acceptance for production retrieval.
- `32-intentional-fallbacks-and-neo4j-plugin-licensing.md` why stub/Louvain/Cypher-degree/legacy-FTS stay; APOC/GDS Community vs Enterprise licensing.
- `33-production-retrieval-live-test-gates.md` live/fuzzer/challenge gates, pythonpath, AuthError skip policy, anti-cascade acceptance.
- `35-wedge-operator-connect-runbook.md` operator connect → ingest → explore/hybrid smoke.
- `36-dead-code-candidates-and-cleanup-loop.md` unused-symbol candidates, MCP contract, live-until-proven exclusions, and closed loop with guidance + cleanup KPIs.
- `37-rpm-session-parallel-sync-feature-specification.md` requirements for RPM-session-gated parallel `agentcore sync` (**implemented**).
- `38-rpm-session-parallel-sync-high-level-design.md` topology: file workers, LLM queue, session registry, LockedStore, CLI/HTTP observe.
- `39-rpm-session-parallel-sync-low-level-design.md` session lifecycle, dual capacity gate, fairness, store concurrency, status API.
- `40-rpm-session-parallel-sync-risks-challenges-and-acceptance.md` challenges, known limits, acceptance gates.
- `41-hybrid-documentation-coverage.md` layered hybrid coverage (AST + living + human + rationale), read/write paths, optional behaviors, no invented edges.
- `42-documentation-catalog-and-lane-cache.md` cached docs frontmatter catalog (tags + closed lane enums) for agent retrieval narrowing.
- `43-wiki-and-graph-composed-retrieval.md` composes Repository Code Wiki (coarse) with graph / hybrid retrieval / hybrid docs (fine) for higher-understanding Q&A — future; not a v1 wedge claim.
- `44-codebase-memory-neo4j-hybrid-feature-specification.md` Codebase-Memory-inspired structural MCP on Neo4j with hybrid escalate (best-quality path; not SQLite).
- `45-codebase-memory-neo4j-hybrid-high-level-design.md` topology and module ownership for structural tools + escalate.
- `46-codebase-memory-neo4j-hybrid-low-level-design.md` algorithms, contracts, and implementation progress checklist.
- `47-codebase-memory-neo4j-hybrid-risks-and-acceptance.md` risks, honesty vs paper metrics, acceptance gates.
- `48-ast-and-lsp-hybrid-parsing-adr.md` accepts AST / tree-sitter as the durable knowledge↔code SoR and reserves LSP for optional edit-session enrichment (not a second graph SoR).
- `49-lsp-edit-session-feature-specification.md` ships IDE-semantic find-refs / definition / rename via local LSP + reconcile.
- `50-sync-cpu-budget-and-store-concurrency-lld.md` CPU percent → workers/embeds/Torch pins; Neo4j bounded store slots; list_symbols without embeddings.
- `51-client-standards-gate-and-watcher-policy.md` AgentCore Client mutable Skip vs Ingest preference for nonconforming docs/code; watcher/flush precedence (`lifecycle_lane: future` until Client UI ships).

## History

- 2026-07-24: Added `51-client-standards-gate-and-watcher-policy.md` (Client standards-gate preference + watcher policy).
- 2026-07-24: Added `50-sync-cpu-budget-and-store-concurrency-lld.md`; corrected Neo4j store concurrency vs exclusive write lock in `03`/`38`/`39` and LiteLLM env knobs.
- 2026-07-23: Added `49-lsp-edit-session-feature-specification.md` and shipped edit-session tools (ADR 48 ID5).
- 2026-07-23: Added `48-ast-and-lsp-hybrid-parsing-adr.md` (AST durable SoR + optional LSP edit layer).
- 2026-07-23: Added `43-wiki-and-graph-composed-retrieval.md` (Wiki + graph composed Q&A / context packs; `lifecycle_lane: future`).
- 2026-07-22: Added `42-documentation-catalog-and-lane-cache.md` (docs catalog CLI/MCP + cache).
- 2026-07-22: Added `41-hybrid-documentation-coverage.md` (hybrid read pack + evidence `docs-suggest-links` write path).
- 2026-07-22: Added RPM-session parallel sync design pack `37`–`40` (`lifecycle_lane: future`; docs only until implementation).
- 2026-07-21: Core product readiness backlog `34` (`ac.doc.ckg.core-product-readiness-phased-backlog`) retired (archived). Durable gates live in `19`/`26`/`31`/`33`, product scope, gap register (GAP-005), and runbook `35`. Do not reuse that `doc_id`.
- 2026-07-21: Added `36-dead-code-candidates-and-cleanup-loop.md` for the unused-candidate / cleanup full loop (guidance + KPIs).

## Code Intelligence Enhancements (current)

Surgical explore packs, framework routes, test links, and risk-scored change review on top of the Phase 7 graph. Reading order: `19` → `21` + `THIRD_PARTY_NOTICES` → `22` → `23` → `24` → `25` → `26`. Prior art is MIT; default is clean-room re-implementation (not vendoring upstream CLIs).

## Production Retrieval Stack (current)

BM25 lexical, Neo4j Lucene / Postgres FTS, real BGE embeddings, RRF hybrid, APOC expand, free Leiden (`scikit-network`) with Louvain fallback. Reading order: `27` → `28` → `29` → `30` → `31`. Intentional keepers + plugin license truth: `32`. Live/fuzzer/challenge test gates: `33`. Temporary core-product readiness phases: `34` (retire after A–E).

## Repository Code Wiki (future)

Holistic, architecture-aware repository documentation (overview, module pages, diagrams, incremental update, admin browse + MCP). Complements symbol-level living documentation. Reading order: `14` → `15` → `16` → `17` → `18` → `20` (ideas + license) → `43` (composed Wiki + graph Q&A). Status: draft / `lifecycle_lane: future` (docs only until implementation).

## Dead-code cleanup loop (current)

Unused-symbol candidates, MCP contract, live-until-proven exclusions, and closed-loop guidance + KPIs. Reading order: `36`.

## RPM-session parallel sync (current)

Parallel `agentcore sync` gated by tracked LiteLLM RPM sessions (start/end), serialized store writer, process-local CLI/HTTP observability. Reading order: `37` → `38` → `39` → `40`.

## Implementation Slice

Phase 7 vertical slice service:

- `backend/services/code-graph-service/` — ingest, hash diff, local docs, graph edges, semantic ranking, generation context, generated-code validation
- Persistence: **Neo4j by default** (`AGENTCORE_CODE_GRAPH_STORE=neo4j`); PostgreSQL rollback via `postgres`; pgvector embeddings + outbox mirror via `AGENTCORE_CODE_GRAPH_DATABASE_URL`
- Contract: `backend/services/code-graph-service/docs/phase-7-api-contract.md`
- Tests: `tests/backend/services/code-graph-service/test_code_graph_service.py`
- Live retrieval gates: `33-production-retrieval-live-test-gates.md` + suites `test_production_retrieval_{live,fuzzer,challenge_live}.py`

```bash
.venv/bin/python -m pytest tests/backend/services/code-graph-service -q
## pythonpath configured in pyproject.toml; optional:
## PYTHONPATH=backend/services/code-graph-service/src .venv/bin/python -m pytest ...
```

## Language Policy (non-negotiable)

**Python must remain supported.** TypeScript, JavaScript, Go, and Rust are also supported via tree-sitter. Details: `10-language-support-policy.md`. Durable ingest vs optional LSP edit enrichment: `48-ast-and-lsp-hybrid-parsing-adr.md`.

## AST vs LSP hybrid (current)

Durable Code-Knowledge Graph edges come from AST ingest only. LSP edit-session tools (`49`) are IDE-semantic and must re-ingest via `reconcile_after_edit`. Reading order: `10` → `48` → `49`.

## Relationship to Other Sections

- `../03-docs-as-code-sync/` covers documentation synchronization and drift detection.
- `../06-technical-logic/03-docs-sync-technical-logic.md` covers AST anchors, doc drift, and CI gates.
- This section adds the explicit Neo4j-backed code graph and graph-guided code generation layer.
- Repository Code Wiki (`14`–`18`, `20`) adds repository-level wiki generation on top of the graph; published pages feed docs-sync.
- Wiki + graph composed retrieval (`43`) defines how wiki narrative and graph/hybrid evidence combine for higher-understanding Q&A after Wiki ships.
- Code Intelligence Enhancements (`19`, `21`–`26`, `THIRD_PARTY_NOTICES`) add explore/risk/routes analytics inspired by MIT prior art.
- Production Retrieval Stack (`27`–`31`) adds BM25/FTS/BGE/APOC/free Leiden for agent search quality.
- Dead-code cleanup loop (`36`) adds unused candidates, MCP contract, and measurement hooks so coding agents remove orphaned predecessors; AgentCore does not mutate the repo.
- AST vs LSP hybrid (`48`–`49`) keeps durable knowledge↔code edges on AST ingest; LSP edit-session tools are IDE-semantic and reconcile via re-ingest.
- RPM-session parallel sync (`37`–`40`) parallel ingest gated by tracked LiteLLM sessions with CLI/HTTP observability.
- Client standards gate + watcher policy (`51`) defines mutable Skip vs Ingest for nonconforming docs when Client/watcher flush cannot ask a TTY prompt.
- `../12-common-context-reuse/` can contribute reusable project guidance to metadata retrieval and context-pack construction.
- `../15-agent-workspace-guidance/` seeds always-on cleanup rule and `agentcore-remove-dead-code` skill for connected coding agents.
- `../09-platform-governance-operations/10-impact-reporting-and-benefit-measurement.md` defines dead-code cleanup KPIs.
