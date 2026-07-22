---
doc_id: ac.doc.gap.technical-implementation-gaps
title: Technical Implementation Gaps
doc_type: gap
status: draft
schema_version: '1.0'
owner: platform-docs
summary: This document captures technical implementation gaps that require deeper design,
  prototyping, benchmarking, or proof-of-concept work.
tags:
- gap
- gap
phase: 10-gap-analysis
canonical_path: docs/10-gap-analysis/03-technical-implementation-gaps.md
lifecycle_lane: future
concern_lane: gap
audience_lane:
- platform-engineering
- agents
authority: informative
visibility: internal
linked_symbols: []
---

# Technical Implementation Gaps

## Purpose

This document captures technical implementation gaps that require deeper design, prototyping, benchmarking, or proof-of-concept work.

## GAP-T01 - AST Hash Stability

The design depends on normalized AST hashes, but normalization rules need language-specific validation.

Questions:

- Which syntax changes should not change the hash?
- Which comments should affect the hash because they contain doc flags?
- How are generated files handled?
- How does parser version affect hash stability?

Resolution output:

- Hash normalization spec per language.
- Regression test corpus.

## GAP-T02 - Call Graph Accuracy

Call graph extraction can be inaccurate in dynamic languages.

Questions:

- How are dynamic dispatch, reflection, dependency injection, and monkey patching handled?
- What confidence level is required for impact analysis?
- When should runtime traces supplement static parsing?

Resolution output:

- Call resolution confidence model.
- Static plus runtime hybrid strategy.

## GAP-T03 - Embedding Storage and Refresh Policy

Embeddings are needed for retrieval, but refresh and invalidation strategy needs definition.

Questions:

- When should embeddings regenerate?
- Are embeddings stored in Neo4j or external vector store?
- How are old embeddings invalidated?
- How are embedding model changes handled?

Partial resolution:

- **Vector index ownership (accelerator role):** optional turbovec ANN replica is documented in `../13-technology-stack-and-platform-decisions/08-turbovec-ann-acceleration-integration.md`. Durable embeddings stay in PostgreSQL+pgvector; turbovec is not SoR.
- **Stage-1 hybrid RAG (code-graph):** kind-filtered pgvector search before ANN, multi-seed Neo4j/store neighborhood expand, and embedding-row delete on non-searchable / orphan / removed-from-file symbols (`code_graph.symbol_embeddings.kind`, `application/queries.py`, `postgres_side.py`). Phase-7 dims remain `vector(16)` until a later model-dim migration.
- Full refresh / model-change re-embed policy for large corpora remains open.

Resolution output:

- Embedding lifecycle policy (Stage-1 invalidation for code-graph: partial; model-change: still open).
- Vector index ownership decision (accelerator path: closed by stack ADR `13/08`; baseline SoR remains pgvector).

## GAP-T04 - Prompt Context Verification

ContextBundles should be source-referenced, but verification logic needs more detail.

Questions:

- How does the system prove a ContextBundle included current state?
- How are omitted high-scoring memory items explained?
- How is prompt safety tested?

Resolution output:

- ContextBundle audit schema.
- Prompt safety test suite.

## GAP-T05 - LLM Judge Determinism

LLM-as-a-Judge is useful but can be inconsistent.

Questions:

- Which policies are eligible for LLM judgment?
- What temperature and output constraints are required?
- How are verdicts reproduced later?
- How are low-confidence verdicts handled?

Resolution output:

- LLM judge operating standard.
- Structured verdict schema.
- Reproducibility policy.

## GAP-T06 - SDK Language, Packaging, And Adapter Harness Finalization

AgentCore now defines the SDK platform and SDK engineering architecture, but the final implementation plan still needs language prioritization, package publishing policy, and adapter harness details.

Questions:

- Which SDK packages ship first: TypeScript, Python, or both in the same milestone?
- Which package registries and naming conventions are used?
- Which generator stack owns OpenAPI, event schema, and config schema outputs?
- How are adapter capabilities declared and validated in the first implementation?
- How are adapter contract tests run locally and in CI?
- How are adapter secrets referenced without exposing secret values?

Resolution output:

- Final SDK release plan.
- Package registry and naming decision.
- Adapter harness implementation plan.
- First adapter implementation plan.

## GAP-T07 - Port Preflight Tool

Port management is documented, but the actual preflight mechanism needs design.

Questions:

- Is port preflight a CLI command, startup library, or script?
- How does it detect owning process cross-platform?
- How does it write resolved port maps?
- How does it integrate with Docker Compose or local orchestration?

Resolution output:

- Port preflight tool spec.
- Local development startup flow.

## GAP-T08 - Test Data and Fixture Strategy

The platform needs realistic test data for graph, memory, rules, broker, and docs drift.

Questions:

- What sample repositories are used?
- How are synthetic agents simulated?
- How are security-sensitive fixtures handled?
- How is multi-tenant isolation tested?

Resolution output:

- Test fixture catalog.
- Synthetic workflow generator.
