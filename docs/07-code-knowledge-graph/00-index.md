# 07 - Code-Knowledge Graph Index

## Purpose

This section adds the Code-Knowledge Graph design to AgentCore. The goal is to build a live graph of the codebase that connects files, classes, functions, methods, imports, calls, inheritance, documentation, embeddings, hashes, and generated code context.

This design extends the existing Docs-as-Code and Technical Logic sections. It focuses specifically on graph-backed code understanding, live documentation generation, and graph-guided code generation.

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

## Relationship to Other Sections

- `../03-docs-as-code-sync/` covers documentation synchronization and drift detection.
- `../06-technical-logic/03-docs-sync-technical-logic.md` covers AST anchors, doc drift, and CI gates.
- This section adds the explicit Neo4j-backed code graph and graph-guided code generation layer.
- `../12-common-context-reuse/` can contribute reusable project guidance to metadata retrieval and context-pack construction.
