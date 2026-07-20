---
doc_id: ac.doc.ckg.code-intel-prior-art-license
title: "21 - Code Intelligence Prior Art Ideas And License"
doc_type: standard
status: draft
schema_version: "1.0"
owner: platform-architecture
summary: >-
  Transferable product and engineering ideas from CodeGraph, code-review-graph,
  and graphify for AgentCore code intelligence, plus mandatory MIT license and
  IP compliance rules (clean-room default).
tags:
  - code-intelligence
  - prior-art
  - license
  - mit
  - compliance
  - codegraph
  - graphify
phase: "07-code-knowledge-graph"
canonical_path: docs/07-code-knowledge-graph/21-code-intelligence-prior-art-ideas-and-license.md
related_docs:
  - ac.doc.codegraph.competitive-intelligence-roadmap-adr
  - ac.doc.ckg.code-intel-feature-spec
  - ac.doc.ckg.code-intel-risks
  - ac.doc.ckg.repository-code-wiki-prior-art-license
external_refs:
  - https://github.com/colbymchenry/codegraph
  - https://github.com/tirth8205/code-review-graph
  - https://github.com/Graphify-Labs/graphify
  - https://opensource.org/licenses/MIT
doc_version: "1.0.0"
audience:
  - engineer
  - architect
  - product
  - security
lifecycle_lane: current
concern_lane: standard
audience_lane:
  - platform-engineering
  - security
  - product
authority: normative
visibility: internal
primary_entities:
  - CodeIntelligenceEnhancement
  - PriorArtIdea
  - LicenseObligation
relations_declared:
  - type: complements
    target: ac.doc.codegraph.competitive-intelligence-roadmap-adr
  - type: complements
    target: ac.doc.ckg.code-intel-feature-spec
  - type: complements
    target: ac.doc.ckg.repository-code-wiki-prior-art-license
chunk_hints:
  strategy: heading_h2
  max_tokens: 800
  overlap_tokens: 64
language: en
security_classification: internal
---

# 21 - Code Intelligence Prior Art Ideas And License

## Purpose

This document catalogs **ideas** AgentCore may adopt to improve Code-Knowledge Graph agent and review workflows, drawn from three public MIT-licensed projects. It states **normative license and IP rules** so engineering never ships non-compliant copies.

This is not legal advice. Before vendoring third-party source or redistributing binaries that include it, counsel must confirm obligations against the then-current upstream `LICENSE` files.

Sibling specs: feature (`22`), HLD (`23`), LLD (`24`), contracts (`25`), risks (`26`). Roadmap ADR: `19`.

## License Snapshot (verified 2026-07-20)

| Source | Role | License | Copyright (upstream LICENSE) | Safe use |
| --- | --- | --- | --- | --- |
| [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) | Local code KG + MCP explore for agents | **MIT** (`LICENSE` on `main`) | Copyright (c) 2026 Colby Mchenry | Ideas freely. Code copy only under MIT. Prefer clean-room on Neo4j |
| [tirth8205/code-review-graph](https://github.com/tirth8205/code-review-graph) | Review-oriented graph, blast radius, risk | **MIT** (`LICENSE` on `main`) | Copyright (c) 2026 Tirth Kanani | Ideas freely. Code copy only under MIT. Prefer clean-room |
| [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | Multi-source KG skill; confidence-tagged edges | **MIT** (`LICENSE` on `v8`) | Copyright (c) 2026 Safi Shamsi | Ideas freely. Code copy only under MIT. Prefer clean-room |

### MIT notice text (obligations)

All three licenses use the standard MIT grant. If AgentCore includes unmodified or modified **source** (or substantial verbatim excerpts) from any of them, distributions **must** retain:

1. The copyright notice for that upstream project.
2. The MIT permission notice (including the warranty disclaimer).
3. SBOM / third-party notices entries (see `THIRD_PARTY_NOTICES.md` in this folder).
4. No implication of endorsement by the upstream authors.

**Default AgentCore policy:** inspire and **re-implement** against AgentCore ports (Neo4j `CodeSymbol`/`CODE_REL`, LiteLLM, MCP gateway). Do **not** add these packages as runtime dependencies unless an ADR explicitly accepts MIT vendoring and SBOM updates.

### What “ideas” means

| Allowed without copying code | Not allowed without MIT compliance + ADR |
| --- | --- |
| Algorithms described in docs/README (Leiden, risk weights, explore budget) | Pasting upstream TypeScript/Python modules into AgentCore |
| UX patterns (single primary MCP tool, stale banners) | Shipping their CLI/MCP binaries inside AgentCore |
| Evaluation methodology concepts (token reduction, co-change grading) | Claiming “powered by CodeGraph/CRG/graphify” without affiliation |
| Independent re-implementation of route regex / test naming heuristics | Scraping proprietary hosted products beyond these MIT repos |

## Idea Catalog (transferable)

Tags: **Adopt** (map into AgentCore), **Adapt** (intent kept, shape changed), **Avoid** (conflicts with platform law).

### A. Agent surgical context (primarily CodeGraph)

| ID | Idea | Tag | AgentCore mapping |
| --- | --- | --- | --- |
| CI-01 | Single primary explore MCP tool vs many narrow tools | Adopt | `agentcore_code_graph_explore` preferred; others secondary |
| CI-02 | Adaptive output budget scaled to repo size | Adopt | `explore_budget_for_file_count` + pack builder |
| CI-03 | Sibling / polymorphic skeletonization (signatures vs full bodies) | Adopt | Explore pack `render: signature\|full` |
| CI-04 | Call-path spine kept verbatim | Adopt | `call_path_ids` + `on_spine` |
| CI-05 | Framework-aware HTTP routes → handler edges | Adopt | `ROUTES_TO` + `SymbolKind.ROUTE` |
| CI-06 | Dynamic-dispatch / bridge synthesis with provenance | Adapt | Wave 3; `metadata.provenance` on heuristic `CODE_REL` |
| CI-07 | File watcher + debounce + staleness banner to agents | Adapt | Wave 3; IDE session freshness, not SQLite daemon |
| CI-08 | Affected tests via transitive imports | Adapt | Wave 1–2; start with `TESTED_BY` conventions |
| CI-09 | FTS5 keyword search | Adapt | BM25 + Neo4j Lucene / Postgres FTS + RRF (`27`–`29`) |
| CI-10 | 100% local SQLite SoR | Avoid | AgentCore SoR remains Neo4j (+ Postgres/pgvector) |

### B. Review and architecture analytics (primarily code-review-graph)

| ID | Idea | Tag | AgentCore mapping |
| --- | --- | --- | --- |
| CI-11 | Leiden communities with weighted edge kinds | Adopt | scikit-network Leiden or Louvain in-process (portability). GDS Community could run Leiden without Enterprise key but is not used for communities — [`32`](32-intentional-fallbacks-and-neo4j-plugin-licensing.md) |
| CI-12 | Auto-split oversized communities (>25% of graph) | Adopt | Post-process after Leiden |
| CI-13 | Execution flows from entry points + BFS on CALLS | Adopt | Domain `flows` + detect_changes |
| CI-14 | Flow criticality weighted score | Adopt | file_spread / external / security / test_gap / depth |
| CI-15 | Change risk score (flows, tests, security, callers, churn) | Adopt | `detect_changes` / `compute_risk_score` |
| CI-16 | `TESTED_BY` edges | Adopt | Convention linker at ingest |
| CI-17 | Hub (degree) and bridge (betweenness) nodes | Adopt | Wave 2; in-process degree + approx betweenness |
| CI-18 | Knowledge gaps (isolated, thin community, untested hotspot) | Adopt | Wave 2 architecture overview |
| CI-19 | Surprise / unexpected coupling scoring | Adapt | Wave 2; pair with edge confidence |
| CI-20 | Hybrid FTS BM25 + embeddings via RRF | Adopt | Shipped — docs `27`–`31` |
| CI-21 | GitHub Action sticky PR risk comment | Adapt | Optional CI job; local-first on runner |
| CI-22 | Circular “recall 1.0” marketing for impact | Avoid | Evaluate with git co-change / human labels |
| CI-23 | Expose 30 MCP tools by default | Avoid | Prefer CI-01 |

### C. Explainability and multi-source map (primarily graphify)

| ID | Idea | Tag | AgentCore mapping |
| --- | --- | --- | --- |
| CI-24 | Edge confidence tiers as first-class UX (`EXTRACTED`/`INFERRED`/`AMBIGUOUS`) | Adapt | Map to AgentCore `exact`/`probable`/`ambiguous`/`unresolved`; always surface in MCP |
| CI-25 | God nodes (high degree, noise-filtered) | Adopt | Wave 2 overview |
| CI-26 | Surprising connections + suggested questions | Adopt | Wave 2 report / MCP |
| CI-27 | Shortest path between two symbols/concepts | Adopt | Wave 2 query |
| CI-28 | Rationale / `# WHY:` / ADR nodes linked to code | Adapt | Extend `DOCUMENTED_BY` / rationale kind |
| CI-29 | Agent skill/hook that prefers graph query before Read | Adapt | Usage-profile + workspace guidance |
| CI-30 | Docs/PDF/video in same graph | Adapt | Docs/SQL first; PDF/video only if product expands |
| CI-31 | Memory/reflect loop from Q&A outcomes | Adapt | Optional; tie to AgentCore memory BC |
| CI-32 | Commit `graph.json` as team SoT | Avoid | Server Neo4j is SoT; exports are artifacts |

## Mapping To Improvement Levers

| Lever | Ideas | Expected improvement |
| --- | --- | --- |
| Fewer agent tool calls / tokens | CI-01–CI-04, CI-29 | Surgical context packs |
| Safer reviews / PRs | CI-13–CI-16, CI-21 | Risk-ranked changed symbols + test gaps |
| Architecture literacy | CI-11–CI-12, CI-17–CI-19, CI-25–CI-27 | Communities, bridges, questions |
| Trust in edges | CI-06, CI-24 | Provenance + confidence in every response |
| Platform fit | Avoid list + Adapt tags | Neo4j SoR, LiteLLM, tenant scope |

## Compliance Checklist (normative)

Before any PR that implements or vendors code-intelligence features:

- [ ] No vendored copy of CodeGraph / code-review-graph / graphify source unless ADR + SBOM + MIT notices approved.
- [ ] If MIT code is copied: retain that project’s copyright + permission notice; update `THIRD_PARTY_NOTICES.md`.
- [ ] Product copy may say “inspired by” / “prior art”; must not claim affiliation or “powered by” those products.
- [ ] Benchmarks do not claim circular graph-derived “100% recall” as customer truth.
- [ ] Secrets, tenant isolation, and LiteLLM-only LLM access remain in force.
- [ ] Re-verify upstream `LICENSE` files if bumping a vendored commit.

## Related Documents

- [`19-competitive-code-intelligence-roadmap-adr.md`](19-competitive-code-intelligence-roadmap-adr.md)
- [`22-code-intelligence-enhancements-feature-specification.md`](22-code-intelligence-enhancements-feature-specification.md)
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
- External: [CodeGraph](https://github.com/colbymchenry/codegraph), [code-review-graph](https://github.com/tirth8205/code-review-graph), [graphify](https://github.com/Graphify-Labs/graphify)
