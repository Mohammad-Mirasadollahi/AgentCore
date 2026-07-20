---
doc_id: ac.doc.codegraph.language-support-policy
title: "10 - Language Support Policy"
doc_type: specification
status: active
schema_version: "1.0"
owner: code-graph-lead
summary: >-
  Normative language matrix for Code-Knowledge Graph ingestion: Python is
  required; TypeScript, JavaScript, Go, and Rust are supported via tree-sitter
  adapters into a shared symbol schema.
tags:
  - code-graph
  - parsers
  - tree-sitter
  - python
  - rust
phase: "07-code-knowledge-graph"
canonical_path: docs/07-code-knowledge-graph/10-language-support-policy.md
related_docs:
  - ac.doc.codegraph.neo4j-migration-plan
  - docs/07-code-knowledge-graph/03-ingestion-and-living-documentation-workflow.md
doc_version: "1.1.0"
audience:
  - engineer
  - architect
  - agent
lifecycle_lane: current
concern_lane: implementation
audience_lane:
  - platform-engineering
  - agents
authority: normative
visibility: internal
primary_entities:
  - LanguageMatrix
  - ParserAdapter
  - CodeSymbol
relations_declared:
  - type: constrains
    target: backend/services/code-graph-service/
  - type: complements
    target: docs/07-code-knowledge-graph/11-neo4j-migration-plan.md
chunk_hints:
  strategy: heading_h2
  max_tokens: 800
  overlap_tokens: 64
language: en
security_classification: internal
---

# 10 - Language Support Policy

## Purpose

Defines which programming languages the Code-Knowledge Graph may ingest, which parsers own each language, and the non-negotiable Python baseline. All supported languages normalize into the same symbol/edge schema so retrieval and generation context remain language-agnostic at the Store port.

## Mandatory Baseline: Python

**Python must remain supported.** It is the required baseline language for the Code-Knowledge Graph.

Rules:

- `LANGUAGE_MATRIX["python"].status` must remain `supported`.
- `LANGUAGE_MATRIX["python"].required` must remain `true`.
- Ingest, hashing, documentation refresh, graph edges, semantic ranking stubs, generation-context packs, and generated-code validation must work for `.py` sources.
- Default ingest language is `python` when callers omit `language`.
- Service startup calls `assert_required_languages_supported()` and fails fast if Python is not supported.
- Neo4j cutover and parser swaps must not regress Python support.

Current Python parser: stdlib `ast` (`parser=stdlib_ast`).

## Supported Languages

| Language   | Status    | Required | Parser        | Extensions                         |
|------------|-----------|----------|---------------|------------------------------------|
| Python     | supported | true     | stdlib_ast    | `.py`                              |
| TypeScript | supported | false    | tree_sitter   | `.ts`, `.tsx`, `.mts`, `.cts`      |
| JavaScript | supported | false    | tree_sitter   | `.js`, `.jsx`, `.mjs`, `.cjs`      |
| Go         | supported | false    | tree_sitter   | `.go`                              |
| Rust       | supported | false    | tree_sitter   | `.rs`                              |

Unsupported languages return a validation error. Planned languages must not be silently skipped with empty graphs.

## Module Ownership

| Concern | Owner |
|---------|-------|
| Language matrix and guards | `code_graph_service.domain.languages` |
| Parser registry | `code_graph_service.domain.parsers` |
| Python adapter | `code_graph_service.domain.parsing` (`parse_python_source`) |
| JS/TS/Go/Rust adapters | `code_graph_service.domain.parsers.{javascript,typescript,go_lang,rust_lang}` |
| Ingest orchestration | `code_graph_service.application.service.CodeGraphService` |

## Multi-Language Repository Behavior

- Ingest is **per file** and carries an explicit `language` field (or extension-based detection via `detect_language_from_path`).
- A polyglot repository may index each supported language independently into one project-scoped graph.
- Cross-language call edges remain best-effort / unresolved until dedicated FFI and package-resolution rules are added.
- Coverage gaps for unsupported extensions must surface as validation failures, not partial corrupt symbols.

## Acceptance Criteria

- Python ingest golden path remains green.
- TypeScript, JavaScript, Go, and Rust each extract at least functions/methods (and classes/structs/traits where applicable), imports, and call names into `ParsedSymbol`.
- `supported_languages()` returns all five languages above.
- `required_languages()` returns only `python`.
- Hash normalization is language-aware (`#` vs `//` / block comments).

## Implementation References

- Matrix: `backend/services/code-graph-service/src/code_graph_service/domain/languages.py`
- Registry: `backend/services/code-graph-service/src/code_graph_service/domain/parsers/__init__.py`
- Contract: `backend/services/code-graph-service/docs/phase-7-api-contract.md`
- Migration: `11-neo4j-migration-plan.md`
