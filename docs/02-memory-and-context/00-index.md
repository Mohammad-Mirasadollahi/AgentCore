# 02 - Memory and Context Index

## Mission

Give agents the right context at the right time while keeping prompts fast, cheap, current, scoped, and low-noise.

## Files

- 01-feature-specification.md defines memory features and functional requirements.
- 02-high-level-design.md defines actors, components, data flow, integrations, and reliability requirements.
- 03-low-level-design.md defines classification, consolidation, weighting, retrieval, decay, and prompt-packing logic.
- 04-data-contracts-and-events.md defines memory entities, events, and WeightProfile contracts.
- 05-risks-challenges-and-acceptance.md defines memory risks and acceptance criteria.
- 06-detailed-section-design.md provides deep rationale, memory lifecycle, retrieval design, edge cases, and phase output.
- 07-autonomous-question-discovery-and-faq-memory.md defines repeated question detection, curiosity scoring, missing documentation discovery, FAQ memory, evidence-backed answer promotion, and human-like knowledge gap handling.
- 08-batched-memory-and-deferred-knowledge-workflows.md defines WorkBatch, deferred memory consolidation, deferred documentation generation, deferred code review, LLM batching decisions, and boundary detection.

## Features Covered

- Three-Tier Memory.
- Memory Consolidation.
- State over Event Context.
- Decay and Garbage Collection.
- Prompt Caching.
- Dynamic Context Injection and RAG.
- Configurable Memory Weighting.
- Autonomous Question Discovery.
- FAQ Memory.
- Curiosity Scoring.
- Missing Documentation Discovery.
- Batched Memory Consolidation.
- Deferred Documentation Generation.
- Deferred Code Review.

## Related Technical Logic

- ../06-technical-logic/02-memory-context-technical-logic.md explains memory classification, consolidation, retrieval scoring, prompt cache invalidation, decay, token budgeting, question memory, FAQ scoring, curiosity scoring, and batched consolidation.

## Optional ANN Acceleration

- ../13-technology-stack-and-platform-decisions/08-turbovec-ann-acceleration-integration.md — ADR: turbovec beside pgvector SoR.
- ../13-technology-stack-and-platform-decisions/11-turbovec-for-rag.md — how to use turbovec in RAG pipelines.
- ../11-logical-implementation-examples/08-turbovec-hybrid-retrieval-example.md — hybrid allowlist retrieval example.
