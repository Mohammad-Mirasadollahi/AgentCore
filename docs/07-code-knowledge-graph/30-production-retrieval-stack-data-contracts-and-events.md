---
doc_id: ac.doc.ckg.prod-retrieval-contracts
title: 30 - Production Retrieval Stack Data Contracts And Events
doc_type: contract
status: active
schema_version: '1.0'
owner: code-graph-lead
summary: HTTP/MCP payload contracts for hybrid BM25+RRF search, path method, architecture
  algorithm, and retrieval transparency fields.
tags:
- contracts
- retrieval
- mcp
- api
phase: 07-code-knowledge-graph
canonical_path: docs/07-code-knowledge-graph/30-production-retrieval-stack-data-contracts-and-events.md
lifecycle_lane: current
concern_lane: contract
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols: []
related_docs:
- ac.doc.ckg.prod-retrieval-feature-spec
- backend/services/code-graph-service/docs/phase-7-api-contract.md
doc_version: 1.0.0
audience:
- engineer
- agent
primary_entities:
- HybridSearchResult
- ArchitectureOverview
- SymbolPathResult
relations_declared:
- type: complements
  target: backend/services/code-graph-service/docs/phase-7-api-contract.md
chunk_hints:
  strategy: heading_h2
  max_tokens: 700
  overlap_tokens: 48
language: en
security_classification: internal
updated_at: '2026-07-24'
---

# 30 - Production Retrieval Stack Data Contracts And Events


## Purpose

HTTP/MCP payload contracts for hybrid BM25+RRF search, path method, architecture algorithm, and retrieval transparency fields.

## HTTP

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/v1/projects/{project_id}/graph/search:hybrid` | BM25 + semantic + FTS RRF |
| POST | `/api/v1/projects/{project_id}/graph/explore` | Includes `retrieval` mode |
| POST | `/api/v1/projects/{project_id}/graph/path` | Includes `method` |
| POST | `/api/v1/projects/{project_id}/graph/architecture-overview` | Includes `algorithm` |
| GET | `/api/v1/projects/{project_id}/graph/neo4j-capabilities` | `apoc`, `gds`, `fulltext`, `gds_enabled`, `gds_concurrency` |

### HybridSearchResult

```json
{
  "query": "string",
  "mode": "bm25|hybrid_rrf_semantic_bm25|hybrid_rrf_fts_semantic_bm25",
  "hits": [
    {
      "symbol_id": "string",
      "score": 0.0,
      "qualified_name": "string",
      "kind": "function",
      "file_path": "string"
    }
  ],
  "channels": { "bm25": 0, "semantic": 0, "fts": 0 },
  "embedding_backend": "string",
  "fts_method": "neo4j.fulltext|postgres.fts|null"
}
```

### SymbolPathResult (additions)

```json
{
  "method": "neo4j_shortest_path|in_memory_bfs",
  "reachable": true
}
```

### ArchitectureOverview (additions)

```json
{
  "algorithm": "scikit_network_leiden|louvain_leiden_refine|isolated_nodes"
}
```

### Structural neighbors (additions)

```json
{
  "expansion": "apoc_expand|store_expand|one_hop",
  "neo4j_capabilities": { "apoc": true, "gds": false, "fulltext": true }
}
```

## MCP (usage profile)

Unchanged tool names; payloads gain the fields above:

- `agentcore_code_graph_hybrid_search`
- `agentcore_code_graph_explore`
- `agentcore_code_graph_path`
- `agentcore_code_graph_architecture_overview`

## Env (operator)

| Variable | Default | Role |
| --- | --- | --- |
| `AGENTCORE_EMBEDDING_PROVIDER` | `local_bge` | `local_bge` \| `stub` \| `litellm` |
| `AGENTCORE_EMBEDDING_MODEL` | `BAAI/bge-large-en-v1.5` | ST model id |
| `AGENTCORE_EMBEDDING_DIMS` | `1024` | pgvector width |
| `AGENTCORE_EMBEDDING_LOCAL_ENABLED` | `true` | Allow local ST |
| `AGENTCORE_CODE_GRAPH_DATABASE_URL` | empty | pgvector + outbox mirror |
| `AGENTCORE_NEO4J_*` | Compose defaults | Structural store + FTS |
| `AGENTCORE_NEO4J_GDS_ENABLED` | `true` | Optional Community `gds.degree` (≤4 cores) |
| `AGENTCORE_NEO4J_GDS_CONCURRENCY` | `4` | Clamped to 1–4 |

Optional extras: `pip install 'agentcore[embeddings]'`, `pip install 'agentcore[graph-analytics]'`.
