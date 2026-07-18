# 03 - Docs-as-Code and Synchronization Index

## Mission

Make documentation, code, decisions, and ownership part of one synchronized knowledge graph so documentation drift is detected before merge.

## Files

- `01-feature-specification.md` defines documentation synchronization features and requirements.
- `02-high-level-design.md` defines actors, components, sync flow, integrations, and reliability requirements.
- `03-low-level-design.md` defines AST anchors, hash generation, frontmatter validation, drift detection, Bloom filter lookup, and CI gate rules.
- `04-data-contracts-and-events.md` defines docs, code symbol, graph, and drift contracts.
- `05-risks-challenges-and-acceptance.md` defines risks and acceptance criteria.
- `06-detailed-section-design.md` provides deep rationale, graph design, AST anchor details, drift behavior, edge cases, and phase output.

## Features Covered

- Documentation Knowledge Graph
- AST Anchoring
- YAML Frontmatter
- Bloom Filter Lookup
- Lightweight y/n Doc Flags

## Related Technical Logic

- `../06-technical-logic/03-docs-sync-technical-logic.md` explains code indexing, AST anchors, documentation graph linking, drift detection, Bloom filters, and CI merge gates.

## Related Authoring Standard

- `../00-master-plan/08-documentation-structure-and-machine-ingest-standard.md` defines how authors must structure files, headings, frontmatter, RAG chunks, GraphRAG relations, and fallback-readable bodies so docs-sync and retrieval stacks can ingest them optimally.
