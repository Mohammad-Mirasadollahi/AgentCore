# code-graph-service

Phase 7 Code-Knowledge Graph vertical slice for AgentCore.

## Owns

- Python file ingestion and symbol extraction (stdlib `ast`)
- Normalized symbol hashing and change detection
- Local documentation generation for **changed symbols only**
- Graph edges: `CONTAINS`, `CALLS`, `IMPORTS`, `INHERITS_FROM`
- Structural neighbor queries and local semantic ranking
- Graph-guided generation context packs (`uses_full_repository=false`)
- Generated-code unknown-symbol validation
- Outbox events `FileIngested`, `SymbolsDocumented`

## Config

`config/code-graph-service.example.env` documents local development settings. Runtime persistence uses the service-owned `code_graph` PostgreSQL schema. The in-memory Store fake and `HeuristicDocGenerator` are limited to unit/transport tests and local deterministic documentation (no external model calls).

## Tests

```bash
PYTHONPATH=backend/services/code-graph-service/src \
  .venv/bin/python -m pytest tests/backend/code-graph-service/test_phase7.py -q
```

## Contract

See `docs/phase-7-api-contract.md`.
