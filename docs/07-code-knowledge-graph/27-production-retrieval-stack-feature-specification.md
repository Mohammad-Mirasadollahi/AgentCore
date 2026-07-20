---
doc_id: ac.doc.ckg.prod-retrieval-feature-spec
title: "27 - Production Retrieval Stack Feature Specification"
doc_type: feature_spec
status: active
schema_version: "1.0"
owner: code-graph-lead
summary: >-
  Production retrieval for code-graph agents: Okapi BM25 lexical search,
  Neo4j Lucene / Postgres FTS, real BGE embeddings with RRF hybrid, APOC
  neighborhood expand, and free scikit-network Leiden communities.
tags:
  - retrieval
  - bm25
  - embeddings
  - apoc
  - leiden
  - feature-specification
phase: "07-code-knowledge-graph"
canonical_path: docs/07-code-knowledge-graph/27-production-retrieval-stack-feature-specification.md
related_docs:
  - ac.doc.ckg.prod-retrieval-hld
  - ac.doc.ckg.prod-retrieval-lld
  - ac.doc.ckg.prod-retrieval-contracts
  - ac.doc.ckg.prod-retrieval-risks
  - ac.doc.ckg.intentional-fallbacks-and-plugin-licensing
  - ac.doc.ckg.code-intel-feature-spec
doc_version: "1.0.0"
audience:
  - engineer
  - architect
  - agent
lifecycle_lane: current
concern_lane: feature
audience_lane:
  - platform-engineering
  - agents
authority: normative
visibility: internal
primary_entities:
  - HybridSearchResult
  - ExplorePack
  - CodeCommunity
relations_declared:
  - type: depends_on
    target: ac.doc.ckg.code-intel-feature-spec
  - type: complements
    target: docs/07-code-knowledge-graph/12-neo4j-runtime-plugins.md
chunk_hints:
  strategy: heading_h2
  max_tokens: 800
  overlap_tokens: 64
language: en
security_classification: internal
---

# 27 - Production Retrieval Stack Feature Specification

## Purpose

Make Code-Knowledge Graph **retrieval production-grade**: keyword search that
actually ranks like search engines, embeddings that are real models (not hash
stubs), multi-hop expansion via free Neo4j APOC, and community detection via
free Leiden — without commercial Neo4j GDS algorithm licenses.

## Goals

1. **BM25 lexical** for in-process ranking (`hybrid_search` / explore seeds).
2. **Store FTS**: Neo4j Lucene fulltext (v2 includes `file_path`) and Postgres
   `tsvector` / `ts_rank_cd` when the respective store is used.
3. **RRF hybrid** of BM25 + semantic + store FTS.
4. **Real embeddings by default**: `AGENTCORE_EMBEDDING_PROVIDER=local_bge`
   (BAAI/bge-large-en-v1.5, 1024-d) with LiteLLM optional and stub fallback.
5. **APOC expand** for neighbors / explore candidate growth when plugins exist.
6. **Free Leiden** via optional `scikit-network`; Louvain fallback otherwise.
7. **Transparency**: responses report `mode`, `embedding_backend`, `fts_method`,
   community `algorithm`, path `method`, neighbor `expansion`.

## Non-Goals

- Neo4j GDS **Enterprise** (paid key). GDS **Community** may be installed for optional `gds.degree` only; communities stay in-process — see [`32`](32-intentional-fallbacks-and-neo4j-plugin-licensing.md).
- GPL `leidenalg` / `igraph` dependencies.
- turbovec as Stage-1 (remains Stage-2 optional accelerator).
- Replacing Neo4j SoR.

## User-visible behaviors

| Surface | Behavior |
| --- | --- |
| `search:hybrid` / MCP hybrid | BM25 + semantic + FTS → RRF; mode string names channels |
| `explore` | Hybrid seeds + CALLS flow + APOC expand when available |
| `neighbors` / structural | `apoc_expand` vs `one_hop` |
| `path` | Neo4j `shortestPath` when store supports it; else in-memory BFS |
| `architecture-overview` | Leiden (scikit-network) or Louvain; `algorithm` field |

## Acceptance sketch

- Unit tests green for BM25 ranking, hybrid modes, communities algorithm tag.
- Without GDS **Enterprise** key (and even without GDS plugin), architecture and expand still work; optional `gds.degree` only when Community plugin loads.
- Stub embeddings only when BGE/LiteLLM unavailable or provider=`stub`.
- Docs `27`–`32` match implemented APIs and intentional keepers.
