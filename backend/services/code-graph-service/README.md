# code-graph-service

Phase 7 Code-Knowledge Graph vertical slice for AgentCore.

## Package layout

```text
code_graph_service/
  domain/          # enums, models, languages, parsing, parsers/, ports, embeddings, docs
  application/     # ingest / queries / generation use cases + CodeGraphService facade
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
- Polyglot project profiling (`language-profile`) that detects related multi-language clusters
- Normalized symbol hashing and change detection
- Local documentation generation for **changed symbols only** (`LlmBackedDocGenerator` via LiteLLM when enabled; heuristic fallback)
- Graph edges: `CONTAINS`, `CALLS`, `IMPORTS`, `INHERITS_FROM`, `DOCUMENTED_BY`, `ROUTES_TO`, `TESTED_BY`
- Call resolution confidence: `exact` / `probable` / `ambiguous` / `unresolved` (import-alias aware)
- Wave 1–3 intelligence: framework routes, `TESTED_BY`, surgical `explore`, risk-scored `detect_changes`, architecture overview, hybrid search, freshness
- Production retrieval: BM25 + Neo4j/Postgres FTS + BGE (default) / LiteLLM / stub via RRF (docs `07-code-knowledge-graph/27`–`31`)
- Local BGE / LiteLLM embeddings for semantic ranking (pgvector when `AGENTCORE_CODE_GRAPH_DATABASE_URL` set; default dims 1024)
- Structural neighbor queries (APOC expand when available) and graph-guided generation context packs (`uses_full_repository=false`)
- Generated-code unknown-symbol validation (call-site focused)
- Outbox events `FileIngested`, `SymbolsDocumented`

## Config

`config/code-graph-service.example.env` documents local development settings.

- Default store: Neo4j (`AGENTCORE_CODE_GRAPH_STORE=neo4j` + `AGENTCORE_NEO4J_*`)
- Rollback / parity store: PostgreSQL schema `code_graph` (`AGENTCORE_CODE_GRAPH_STORE=postgres`)
- With `AGENTCORE_CODE_GRAPH_DATABASE_URL`: pgvector `symbol_embeddings` + Postgres outbox mirror (relay-compatible)
- Structural parity helper: `domain/parity.py` (`compare_stores`, `ingest_both_and_compare`)
- Canonical Neo4j projection: `CodeSymbol` + `CODE_REL` (see `docs/07-code-knowledge-graph/13-codesymbol-projection-adr.md`)
- Production embeddings: `AGENTCORE_EMBEDDING_PROVIDER=local_bge` (optional extra `embeddings`); `LocalEmbeddingStub` is test/fallback only
- Optional Leiden: extra `graph-analytics` (`scikit-network`); otherwise in-process Louvain
- Optional Neo4j GDS degree: `AGENTCORE_NEO4J_GDS_ENABLED=true` (default), concurrency ≤ 4 Community cores

## Tests

```bash
PYTHONPATH=backend/services/code-graph-service/src \
  .venv/bin/python -m pytest tests/backend/services/code-graph-service/ -q
```

## Contract

See `docs/phase-7-api-contract.md`. Language policy: `docs/07-code-knowledge-graph/10-language-support-policy.md`.
