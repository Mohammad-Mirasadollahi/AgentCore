# code-graph-service

Phase 7 Code-Knowledge Graph vertical slice for AgentCore.

## Owns

- Python file ingestion and symbol extraction (stdlib `ast`; language matrix hook for planned tree-sitter languages)
- Normalized symbol hashing and change detection
- Local documentation generation for **changed symbols only**
- Graph edges: `CONTAINS`, `CALLS`, `IMPORTS`, `INHERITS_FROM`, `DOCUMENTED_BY`
- Call resolution confidence: `exact` / `probable` / `ambiguous` / `unresolved` (import-alias aware)
- Local embedding stub for semantic ranking (swap point for pgvector)
- Structural neighbor queries and graph-guided generation context packs (`uses_full_repository=false`)
- Generated-code unknown-symbol validation (call-site focused)
- Outbox events `FileIngested`, `SymbolsDocumented`

## Config

`config/code-graph-service.example.env` documents local development settings. Runtime persistence uses the service-owned `code_graph` PostgreSQL schema. The in-memory Store fake, `HeuristicDocGenerator`, and `LocalEmbeddingStub` are limited to unit/transport tests and local deterministic docs/embeddings (no external model calls). Neo4j remains the design target; this slice does not require a Neo4j runtime.

## Tests

```bash
PYTHONPATH=backend/services/code-graph-service/src \
  .venv/bin/python -m pytest tests/backend/code-graph-service/test_phase7.py -q
```

## Contract

See `docs/phase-7-api-contract.md`.
