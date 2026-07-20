# code-graph-service

Phase 7 Code-Knowledge Graph vertical slice for AgentCore.

## Package layout

```text
code_graph_service/
  domain/          # enums, models, languages, parsing, parsers/, ports, embeddings, docs
  application/     # CodeGraphService use cases
  core.py          # compatibility re-exports (prefer domain/application imports)
  postgres_store.py
  neo4j_store.py
  api.py
  bootstrap.py
  testing.py
```

## Owns

- Python file ingestion via stdlib `ast` (**required** language)
- TypeScript, JavaScript, Go, and Rust ingestion via tree-sitter adapters (`domain/parsers/`)
- **Mandatory Python support** — `required=true` in the language matrix; startup fails if Python is not supported
- Normalized symbol hashing and change detection
- Local documentation generation for **changed symbols only**
- Graph edges: `CONTAINS`, `CALLS`, `IMPORTS`, `INHERITS_FROM`, `DOCUMENTED_BY`
- Call resolution confidence: `exact` / `probable` / `ambiguous` / `unresolved` (import-alias aware)
- Local embedding stub for semantic ranking (swap point for pgvector)
- Structural neighbor queries and graph-guided generation context packs (`uses_full_repository=false`)
- Generated-code unknown-symbol validation (call-site focused)
- Outbox events `FileIngested`, `SymbolsDocumented`

## Config

`config/code-graph-service.example.env` documents local development settings.

- Default store: PostgreSQL schema `code_graph` (`AGENTCORE_CODE_GRAPH_STORE=postgres`)
- Optional store: Neo4j (`AGENTCORE_CODE_GRAPH_STORE=neo4j` + `AGENTCORE_NEO4J_*`)
- The in-memory Store fake, `HeuristicDocGenerator`, and `LocalEmbeddingStub` are limited to unit/transport tests and local deterministic docs/embeddings (no external model calls)

## Tests

```bash
PYTHONPATH=backend/services/code-graph-service/src \
  .venv/bin/python -m pytest tests/backend/services/code-graph-service/ -q
```

## Contract

See `docs/phase-7-api-contract.md`. Language policy: `docs/07-code-knowledge-graph/10-language-support-policy.md`.
