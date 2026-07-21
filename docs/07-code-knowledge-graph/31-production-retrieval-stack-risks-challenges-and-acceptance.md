---
doc_id: ac.doc.ckg.prod-retrieval-risks
title: "31 - Production Retrieval Stack Risks Challenges And Acceptance"
doc_type: specification
status: active
schema_version: "1.0"
owner: code-graph-lead
summary: >-
  Risks, license constraints, and acceptance gates for the production retrieval
  stack (BM25, FTS, BGE, APOC, free Leiden).
tags:
  - risks
  - acceptance
  - license
  - retrieval
phase: "07-code-knowledge-graph"
canonical_path: docs/07-code-knowledge-graph/31-production-retrieval-stack-risks-challenges-and-acceptance.md
related_docs:
  - ac.doc.ckg.prod-retrieval-feature-spec
  - ac.doc.ckg.prod-retrieval-lld
  - ac.doc.ckg.prod-retrieval-live-test-gates
doc_version: "1.0.0"
audience:
  - engineer
  - architect
  - operator
lifecycle_lane: current
concern_lane: risk
audience_lane:
  - platform-engineering
  - operators
authority: normative
visibility: internal
primary_entities:
  - AcceptanceGate
relations_declared:
  - type: depends_on
    target: ac.doc.ckg.prod-retrieval-feature-spec
chunk_hints:
  strategy: heading_h2
  max_tokens: 600
  overlap_tokens: 40
language: en
security_classification: internal
---

# 31 - Production Retrieval Stack Risks Challenges And Acceptance

## Risks

| ID | Risk | Mitigation |
| --- | --- | --- |
| R-01 | Agents believe stub embeddings are semantic | Report `embedding_backend`; default provider `local_bge` |
| R-02 | Neo4j FTS missing after upgrade | Create v1+v2 indexes in `ensure_schema`; degrade to BM25 |
| R-03 | APOC not installed | One-hop fallback; capabilities probe |
| R-04 | GDS commercial confusion | Doc [`32`](32-intentional-fallbacks-and-neo4j-plugin-licensing.md): Community GDS is free (4-core); Enterprise key not required. Communities stay in-process. |
| R-05 | GPL contamination via leidenalg | Forbidden; scikit-network (BSD) optional only |
| R-06 | BM25 zero scores on tiny corpora | Lucene-style positive IDF in-process |
| R-07 | Model download / disk for BGE | Cache dir `AGENTCORE_EMBEDDING_CACHE_DIR`; stub fallback |
| R-08 | Postgres FTS column absent | Migration `0006`; query falls back to on-the-fly tsvector |
| R-09 | Live suite AuthError looks like ~50 failures | Doc [`33`](33-production-retrieval-live-test-gates.md): skip policy + `pythonpath`; never ERROR-cascade module fixtures |

## License inventory (retrieval extras)

| Component | License | Role |
| --- | --- | --- |
| `rank-bm25` | Apache-2.0 | Optional accelerator for large BM25 corpora |
| `scikit-network` | BSD | Optional Leiden |
| Neo4j APOC Core | Neo4j plugin (Community-compatible install) | Path expand |
| Neo4j GDS | **Community** plugin free (all algos, 4-core limit); **Enterprise** paid | AgentCore may call `gds.degree` optionally; never requires Enterprise; communities not on GDS — see [`32`](32-intentional-fallbacks-and-neo4j-plugin-licensing.md) |
| Sentence-Transformers / BGE weights | Model card / Apache-2.0 family (verify per model) | Local embeddings |

## Acceptance gates

- [x] BM25 lexical ranks relevant symbols in unit tests.
- [x] Hybrid response includes `mode`, `channels`, `embedding_backend`.
- [x] Neo4j fulltext v2 schema statement present; Lucene query OR-based.
- [x] Postgres FTS migration `0006_symbol_fts.sql` + `PostgresStore.fulltext_search`.
- [x] Explore uses APOC expand when available.
- [x] Path reports `method`; architecture reports `algorithm`.
- [x] Communities prefer scikit-network Leiden; Louvain fallback without GDS.
- [x] Docs `27`–`31` + index entry; code↔doc field names match.
- [x] Live/fuzzer/challenge gates documented in `33`; AuthError cascades skipped not ERROR-flooded; `pythonpath` in pyproject.
- [x] No GPL leidenalg/igraph dependency.

## Open gaps

| Gap | Notes |
| --- | --- |
| Offline eval harness (nDCG on real repos) | Follow-up |
| Watcher daemon for freshness | Session pending-sync already shipped |
| Force BGE preload at process start | Optional ops knob |
