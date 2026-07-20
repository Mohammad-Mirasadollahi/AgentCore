# Code-Knowledge Graph — Neo4j Migration Plan

## Purpose

Plan the cutover from the Phase 7 PostgreSQL `code_graph` projection to Neo4j as the production structural graph store, without regressing mandatory Python language support.

## Current State

- Phase 7 behavioral slice is implemented in `backend/services/code-graph-service/`.
- Default persistence is PostgreSQL (`AGENTCORE_CODE_GRAPH_STORE=postgres`).
- Neo4j adapter exists (`neo4j_store.py`) and Compose can start Neo4j under profile `core`.
- Python is **required** and currently supported via stdlib `ast`. TypeScript, JavaScript, Go, and Rust are supported via tree-sitter adapters.

## Non-Negotiable Gate: Python Support

Before any production cutover:

1. Python ingest round-trip must pass on Neo4j (symbols, CONTAINS/CALLS/IMPORTS/INHERITS_FROM/DOCUMENTED_BY).
2. Hash-based change detection must document only changed Python symbols.
3. Generation-context packs and generated-code validation must work for Python repositories.
4. `required_languages()` must include `python` and `assert_required_languages_supported()` must pass at service startup.

A Neo4j cutover that breaks Python support is a release blocker.

## Cutover Steps

1. Run Neo4j locally via Compose (`--profile core`) and point a staging service at `AGENTCORE_CODE_GRAPH_STORE=neo4j`.
2. Replay or dual-write a representative Python repository through ingest.
3. Compare symbol counts, edge counts, and sample neighbor queries against the Postgres projection.
4. Keep outbox consumers compatible (`FileIngested`, `SymbolsDocumented`).
5. After language-matrix expansion (or an explicit architecture decision), switch production default store to Neo4j.
6. Retain Postgres for embeddings (pgvector) and any non-graph operational tables.

## Rollback

Set `AGENTCORE_CODE_GRAPH_STORE=postgres` and restart the service. Neo4j data remains intact for later retry; do not drop the Postgres `code_graph` schema until Neo4j has been the default for at least one full release cycle.

## Related Artifacts

- Schema design: `02-neo4j-schema-design.md`
- Language policy: `10-language-support-policy.md`
- Gap register: `GAP-011` in `../10-gap-analysis/01-gap-register.md`
- Adapter: `backend/services/code-graph-service/src/code_graph_service/neo4j_store.py`
- Constraints: `backend/platform/persistence/neo4j/cypher/0001_code_graph_constraints.cypher`
