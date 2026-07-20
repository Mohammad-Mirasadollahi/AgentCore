# 07 - Code-Knowledge Graph Index

## Purpose

This section adds the Code-Knowledge Graph design to AgentCore. The graph is the core wedge mechanism: connect a repository, understand it as structured knowledge, and improve connected AI coding outputs through task-scoped context packs.

This design extends the existing Docs-as-Code and Technical Logic sections. It focuses specifically on graph-backed code understanding, live documentation generation, and graph-guided code generation. Product positioning lives in `../00-master-plan/01-product-scope-and-feature-catalog.md`.

## Files

- `01-vision-and-scope.md` defines the purpose, positioning, and expected benefits of the Code-Knowledge Graph.
- `02-neo4j-schema-design.md` defines graph nodes, relationships, properties, constraints, and indexing strategy.
- `03-ingestion-and-living-documentation-workflow.md` defines the real-time ingestion, parsing, hashing, documentation, and graph upsert workflow.
- `04-graph-guided-code-generation-workflow.md` defines how AI code generation retrieves context from the graph instead of reading the whole repository.
- `05-token-optimization-and-model-routing.md` defines hash-based diffing, smart triggers, tiered LLM routing, hierarchical summaries, and cheap embeddings.
- `06-technical-implementation-logic.md` defines implementation-level algorithms, pseudo-code, failure handling, and integration points.
- `07-metadata-first-code-understanding.md` defines the metadata-first architecture that lets agents inspect compact code metadata before reading source code.
- `08-code-metadata-schema-and-lifecycle.md` defines low-level metadata records, lifecycle, freshness states, confidence rules, and source escalation policy.
- `09-context-pack-retrieval-and-agent-workflow.md` defines context packs, retrieval algorithms, agent workflows, use cases, metrics, and safety rules.
- `10-language-support-policy.md` defines mandatory Python support and the planned language matrix.
- `11-neo4j-migration-plan.md` defines Postgres → Neo4j cutover steps without regressing Python.

## Implementation Slice

Phase 7 vertical slice service:

- `backend/services/code-graph-service/` — ingest, hash diff, local docs, graph edges, semantic ranking, generation context, generated-code validation
- Persistence: PostgreSQL projection by default; Neo4j via `AGENTCORE_CODE_GRAPH_STORE=neo4j` (`neo4j_store.py`)
- Contract: `backend/services/code-graph-service/docs/phase-7-api-contract.md`
- Tests: `tests/backend/services/code-graph-service/test_code_graph_service.py`

```bash
PYTHONPATH=backend/services/code-graph-service/src .venv/bin/python -m pytest tests/backend/services/code-graph-service -q
```

## Language Policy (non-negotiable)

**Python must remain supported.** TypeScript, JavaScript, Go, and Rust are also supported via tree-sitter. Details: `10-language-support-policy.md`.

## Relationship to Other Sections

- `../03-docs-as-code-sync/` covers documentation synchronization and drift detection.
- `../06-technical-logic/03-docs-sync-technical-logic.md` covers AST anchors, doc drift, and CI gates.
- This section adds the explicit Neo4j-backed code graph and graph-guided code generation layer.
- `../12-common-context-reuse/` can contribute reusable project guidance to metadata retrieval and context-pack construction.
