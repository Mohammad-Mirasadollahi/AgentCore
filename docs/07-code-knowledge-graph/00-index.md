# 07 - Code-Knowledge Graph Index

## Purpose

This section adds the Code-Knowledge Graph design to AgentCore. The graph is the core wedge mechanism: connect a repository, understand it as structured knowledge, and improve connected AI coding outputs through task-scoped context packs.

This design extends the existing Docs-as-Code and Technical Logic sections. It focuses specifically on graph-backed code understanding, live documentation generation, and graph-guided code generation. Product positioning lives in `../00-master-plan/01-product-scope-and-feature-catalog.md`.

## Files

- `01-vision-and-scope.md` defines the purpose, positioning, and expected benefits of the Code-Knowledge Graph.
- `02-neo4j-schema-design.md` defines graph nodes, relationships, properties, constraints, and indexing strategy.
- `03-ingestion-and-living-documentation-workflow.md` defines the real-time ingestion, parsing, hashing, documentation, and graph upsert workflow.
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

## Code Intelligence Enhancements (current)

Surgical explore packs, framework routes, test links, and risk-scored change review on top of the Phase 7 graph. Reading order: `19` → `21` + `THIRD_PARTY_NOTICES` → `22` → `23` → `24` → `25` → `26`. Prior art is MIT; default is clean-room re-implementation (not vendoring upstream CLIs).

## Production Retrieval Stack (current)

BM25 lexical, Neo4j Lucene / Postgres FTS, real BGE embeddings, RRF hybrid, APOC expand, free Leiden (`scikit-network`) with Louvain fallback. Reading order: `27` → `28` → `29` → `30` → `31`. Intentional keepers + plugin license truth: `32`. Live/fuzzer/challenge test gates: `33`.

## Repository Code Wiki (future)

Holistic, architecture-aware repository documentation (overview, module pages, diagrams, incremental update, admin browse + MCP). Complements symbol-level living documentation. Reading order: `14` → `15` → `16` → `17` → `18` → `20` (ideas + license). Status: draft / `lifecycle_lane: future` (docs only until implementation).

## Implementation Slice

Phase 7 vertical slice service:

- `backend/services/code-graph-service/` — ingest, hash diff, local docs, graph edges, semantic ranking, generation context, generated-code validation
- Persistence: **Neo4j by default** (`AGENTCORE_CODE_GRAPH_STORE=neo4j`); PostgreSQL rollback via `postgres`; pgvector embeddings + outbox mirror via `AGENTCORE_CODE_GRAPH_DATABASE_URL`
- Contract: `backend/services/code-graph-service/docs/phase-7-api-contract.md`
- Tests: `tests/backend/services/code-graph-service/test_code_graph_service.py`
- Live retrieval gates: `33-production-retrieval-live-test-gates.md` + suites `test_production_retrieval_{live,fuzzer,challenge_live}.py`

```bash
.venv/bin/python -m pytest tests/backend/services/code-graph-service -q
# pythonpath configured in pyproject.toml; optional:
# PYTHONPATH=backend/services/code-graph-service/src .venv/bin/python -m pytest ...
```

## Language Policy (non-negotiable)

**Python must remain supported.** TypeScript, JavaScript, Go, and Rust are also supported via tree-sitter. Details: `10-language-support-policy.md`.

## Relationship to Other Sections

- `../03-docs-as-code-sync/` covers documentation synchronization and drift detection.
- `../06-technical-logic/03-docs-sync-technical-logic.md` covers AST anchors, doc drift, and CI gates.
- This section adds the explicit Neo4j-backed code graph and graph-guided code generation layer.
- Repository Code Wiki (`14`–`18`, `20`) adds repository-level wiki generation on top of the graph; published pages feed docs-sync.
- Code Intelligence Enhancements (`19`, `21`–`26`, `THIRD_PARTY_NOTICES`) add explore/risk/routes analytics inspired by MIT prior art.
- Production Retrieval Stack (`27`–`31`) adds BM25/FTS/BGE/APOC/free Leiden for agent search quality.
- `../12-common-context-reuse/` can contribute reusable project guidance to metadata retrieval and context-pack construction.
