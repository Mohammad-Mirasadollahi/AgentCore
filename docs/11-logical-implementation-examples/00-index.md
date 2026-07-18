# 11 - Logical Implementation Examples Index

## Purpose

This section explains AgentCore through concrete implementation-oriented examples. It is written for engineers who need to understand how the design behaves before they start coding.

The earlier sections define architecture, contracts, technical logic, governance, and gaps. This section turns those ideas into practical scenarios with inputs, processing steps, outputs, records, state changes, and edge cases.

## Files

- `01-end-to-end-password-migration-example.md` shows how all major systems work together for a password hashing migration.
- `02-memory-and-context-example.md` shows current-state memory, forgotten-memory weighting, retrieval, and prompt bundle creation.
- `03-docs-and-code-graph-example.md` shows code ingestion, documentation drift, AST hashing, Neo4j graph updates, and graph-guided code generation.
- `04-rule-engine-and-human-approval-example.md` shows policy evaluation, deterministic checks, LLM judge use, escalation, and approval outcomes.
- `05-interoperability-and-broker-example.md` shows Universal Agent JSON, broker routing, IDE notification, adapter behavior, and dead-letter handling.
- `06-developer-implementation-checklist.md` gives an engineering checklist for implementing each subsystem.

## How to Use This Section

Read this section after the technical logic documents. It should help engineers answer:

- What input does the subsystem receive?
- Which records are created?
- Which events are emitted?
- Which state changes happen?
- Which errors or edge cases must be handled?
- What should be tested before implementation is considered complete?
