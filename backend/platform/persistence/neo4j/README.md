# Neo4J

Path: `backend/platform/persistence/neo4j`

## Purpose

Graph persistence integration boundary for the Code-Knowledge Graph. Neo4j stores structural code relationships. Semantic embeddings remain in PostgreSQL pgvector.

## Modular Boundary

This directory is part of the AgentCore backend modular architecture. It must expose behavior through documented contracts, public interfaces, configuration, or events. It must not import private internals from sibling modules.

## Allowed Contents

- README and design notes for this boundary.
- Cypher schema / constraint scripts under `cypher/`.
- Shared helpers that belong to this persistence boundary.
- Subdirectories that follow the backend structure standard.

## Runtime Adapter

The Phase 7 service adapter lives in:

- `backend/services/code-graph-service/src/code_graph_service/neo4j_store.py`

Select it with:

```bash
AGENTCORE_CODE_GRAPH_STORE=neo4j
AGENTCORE_NEO4J_URI=bolt://127.0.0.1:32287
AGENTCORE_NEO4J_USER=neo4j
AGENTCORE_NEO4J_PASSWORD=<local-secret>
AGENTCORE_NEO4J_DATABASE=neo4j
```

Schema constraints in `cypher/0001_code_graph_constraints.cypher` are applied by `Neo4jStore.ensure_schema()` on startup. Do not bind that directory under `/var/lib/neo4j/` in Compose; Neo4j chowns its home tree and a read-only mount prevents startup.

## Language Policy

Python is a **required** (mandatory) code-graph language. The Neo4j cutover must not regress Python ingest, symbol hashing, call/import edges, or generation-context packs.

## Rules

- Keep ownership clear and local to this boundary.
- Do not hard-code ports, credentials, tenant IDs, project IDs, model names, provider endpoints, or feature behavior.
- Prefer dependency inversion: domain and application logic should not depend on infrastructure implementation details.
- Use shared packages only for stable contracts or cross-cutting primitives.
- Add or update tests and documentation when this boundary receives implementation code.

## Status

Active scaffold with Cypher constraints. Service-owned `Neo4jStore` implements the Code Graph `Store` port. Compose profile `core` can start Neo4j; default Phase 7 slice still uses PostgreSQL unless `AGENTCORE_CODE_GRAPH_STORE=neo4j`.
