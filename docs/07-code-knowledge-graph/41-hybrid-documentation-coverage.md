---
doc_id: ac.doc.ckg.hybrid-documentation-coverage
title: Hybrid Documentation Coverage
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-docs
summary: Normative hybrid model for AgentCore documentation coverage of code symbols.
  Layers are AST (always after ingest), living LLM/heuristic docs, human Markdown via
  evidence linked_symbols, and optional in-source rationale. Read path merges layers;
  write path suggests evidence tokens only; edges only after sync resolve. Optional
  behaviors (docs-root, include-all, skip without frontmatter, deferred LLM pairing)
  are specified without inventing DOCUMENTED_BY.
tags:
- standard
- ckg
- hybrid
- documentation
- linked_symbols
phase: 07-code-knowledge-graph
canonical_path: docs/07-code-knowledge-graph/41-hybrid-documentation-coverage.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols:
- backend/services/code-graph-service/src/code_graph_service/domain/hybrid_doc_coverage.py::build_symbol_doc_coverage
- backend/services/code-graph-service/src/code_graph_service/application/generation.py::GenerationUseCases
- backend/packages/agentcore_cli/docs_link_suggest.py::extract_evidence_link_tokens
- backend/packages/agentcore_cli/docs_link_suggest.py::suggest_links_for_markdown
- backend/packages/agentcore_cli/docs_link_suggest.py::suggest_links_for_tree
- backend/packages/agentcore_cli/docs_link_suggest.py::apply_suggested_links
- backend/packages/agentcore_cli/commands/docs_suggest_links.py::cmd_docs_suggest_links
related_docs:
- ac.doc.ckg.ingestion-and-living-documentation-workflow
- ac.doc.ckg.context-pack-retrieval-and-agent-workflow
- ac.doc.ckg.graph-guided-code-generation-workflow
- ac.doc.agents.team-handout-agentcore-documentation-complete
language: en
security_classification: internal
---

# Hybrid Documentation Coverage

## Purpose

Define how AgentCore covers a code symbol with **layered documentation** so that missing
optional layers do not leave agents without context. This standard is the SSOT for the
hybrid **read path** (`generation_context.hybrid_documentation`) and the hybrid **write
path** (`agentcore docs-suggest-links`). It also names every **optional** behavior so
operators and agents do not invent graph edges or silent shortcuts.

## Goals and Non-Goals

### Goals

- Always expose AST neighbor structure for ingested symbols.
- Prefer human Markdown when Phase 2 has resolved evidence `linked_symbols`.
- Fall back through living docs → rationale → AST when higher layers are absent.
- Keep link suggestions **evidence-only** (path citations / `path::Symbol` on disk).
- Document optional flags and skip cases so dry-run / apply behavior is predictable.

### Non-Goals

- NLP or embedding auto-pairing that writes `DOCUMENTED_BY` without resolve.
- Inventing symbol names that are not evidenced in Markdown or on disk.
- Replacing Full-tier authoring law or Phase 2 sync semantics.
- Requiring human docs, living LLM docs, or `# WHY:` comments for hybrid to function.

## Layer Model

| Layer | Required? | Source | Agent effect when present | When absent |
| --- | --- | --- | --- | --- |
| **AST** | Yes (after Phase 1 ingest) | Symbol + structural edges (`CALLS`, `IMPORTS`, `CONTAINS`, `INHERITS_FROM`, `ROUTES_TO`, `TESTED_BY`) | Neighbor list in hybrid pack | Symbol not ingested → out of scope for this pack |
| **Living** | Optional | Symbol `ai_documentation` and/or living `DOCUMENTED_BY` docs | Snippets when preferred | Prefer rationale, else AST |
| **Human** | Optional | `doc:human:…` via resolved `linked_symbols` after `agentcore sync` Phase 2 | Highest preference for prompt snippets | Prefer living → rationale → AST |
| **Rationale** | Optional | `# WHY:` / `# NOTE:` / `# HACK:` → `RATIONALE` + `DOCUMENTED_BY` from file (or symbol) | Enrichment snippets | Prefer AST |

**Preference order (prompt snippets):** `human` → `living` → `rationale` → `ast`.

Pack fields (read path):

| Field | Meaning |
| --- | --- |
| `coverage` | Booleans for `ast` / `living` / `human` / `rationale` |
| `active_layers` | Layers present, in preference order |
| `gaps` | Optional layers not present (`living`, `human`, `rationale`) |
| `fallback_chain` | Fixed preference list |
| `preferred_layer` | First present layer in the chain |
| `layers.*` | Concrete neighbors / doc views (deduped by `symbol_id`) |
| `preferred_snippets` | Truncated texts from the preferred layer |
| `optional` | Operator hints for filling gaps (including deferred LLM pairing) |
| `invents_edges` | Always `false` on the read path |

## Read Path

Entry: `build_generation_context` → `build_symbol_doc_coverage`.

MCP tool: `agentcore_code_graph_generation_context` returns the same pack under
`hybrid_documentation` and a short hybrid line in `prompt_context`.

```mermaid
flowchart TD
  seed[Seed symbol after Phase 1] --> pack[build_symbol_doc_coverage]
  pack --> human{Human DOCUMENTED_BY?}
  human -->|yes| preferH[preferred_layer = human]
  human -->|no| living{Living docs or ai_documentation?}
  living -->|yes| preferL[preferred_layer = living]
  living -->|no| rat{Rationale nodes?}
  rat -->|yes| preferR[preferred_layer = rationale]
  rat -->|no| preferA[preferred_layer = ast]
  preferH --> out[generation_context.hybrid_documentation]
  preferL --> out
  preferR --> out
  preferA --> out
```

| Step | Actor | Action | Outcome |
| --- | --- | --- | --- |
| 1 | Agent / CLI / MCP | Request generation context for a seed | Service loads seed + edges |
| 2 | Hybrid pack | Collect human / living / rationale / AST neighbors | Deduped layer lists |
| 3 | Hybrid pack | Choose preferred layer by chain | Snippets for prompts |
| 4 | Caller | Use pack; may still open source | No new graph edges |

## Write Path (evidence suggestions)

Command: `agentcore docs-suggest-links`.

| Mode | Behavior |
| --- | --- |
| Default dry-run | Scan `--docs-root` (default `docs`), report files with **new** evidence tokens |
| `--path FILE` | Single file; always reports that file (including zero suggestions) |
| `--docs-root DIR` | Optional alternate tree (e.g. `backend/docs`) |
| `--include-all` | Include files with zero new suggestions (already linked / no evidence) |
| `--apply` | Merge suggested tokens into YAML `linked_symbols` only |
| `--json` | Machine-readable report |

**Hard rules:**

1. Tokens come only from path citations that resolve on disk (backtick `` `path` `` /
   `` `path::Symbol` ``, or the same path without backticks), where the file exists.
2. `--apply` **never** creates Neo4j edges; only Phase 2 `agentcore sync` does, and only for tokens that resolve.
3. `--apply` on Markdown **without** YAML frontmatter → `skipped_no_frontmatter` (no silent invent of frontmatter).
4. Unresolved tokens after sync still create **no** `DOCUMENTED_BY`.

```mermaid
flowchart LR
  cite[Path citation in Markdown] --> suggest[docs-suggest-links]
  suggest --> fm[Optional --apply to linked_symbols]
  fm --> sync[agentcore sync Phase 2]
  sync --> resolve{Token resolves?}
  resolve -->|yes| edge[DOCUMENTED_BY]
  resolve -->|no| noEdge[No edge]
```

| Step | Actor | Action | Outcome |
| --- | --- | --- | --- |
| 1 | Author | Cite real code paths in the body | Evidence on disk |
| 2 | Operator | Dry-run `docs-suggest-links` | Suggested `path::Symbol` list |
| 3 | Operator | Review; optional `--apply` | Frontmatter updated or skipped |
| 4 | Operator | `agentcore docs-standards` then `agentcore sync` | Edges only for resolved tokens |

## Optional Behaviors (explicit)

These are **supported or deferred** options. Hybrid works without them.

| Optional item | Status | Behavior |
| --- | --- | --- |
| Human Markdown + `linked_symbols` | Supported | Best prompt preference when resolved |
| Living LLM / heuristic `ai_documentation` | Supported when ingest fills it | Mid preference |
| `# WHY:` / `# NOTE:` / `# HACK:` | Supported on ingest | Rationale layer |
| `--docs-root` | Supported | Scan non-default doc trees |
| `--include-all` | Supported | Full scan visibility |
| Apply without frontmatter | Supported skip | Report `skipped_no_frontmatter`; do not invent FM |
| Already-linked evidence | Supported | Listed as `already_linked`; not re-suggested |
| Missing file for citation | Supported omit | Token not suggested (never invented) |
| Body-tier Markdown without Full-tier FM | Sync indexes provisionally | No `DOCUMENTED_BY` until FM + resolve |
| LLM / embedding free-form doc↔symbol pairing | **Deferred** | May *suggest* for humans later; **must not** auto-write `DOCUMENTED_BY` without evidence resolve. Use `docs-suggest-links` for evidence tokens today |

## Operator Checklist

1. Write or fix Full-tier Markdown (authoring law).
2. Cite real code paths in the body when the doc explains code.
3. `agentcore docs-suggest-links` (dry-run) → review → optional `--apply`.
4. `agentcore docs-standards` → zero issues.
5. Optional: add `# WHY:` in source for rationale coverage.
6. `agentcore sync` so Phase 1 + Phase 2 refresh AST / living / human edges.
7. Agents / operators: `agentcore_code_graph_generation_context` (MCP) or
   `agentcore graph generation-context --symbol-id …` and read `hybrid_documentation`.

## Verification

| Check | How |
| --- | --- |
| Read pack prefers human | Unit: `tests/backend/services/code-graph-service/test_hybrid_doc_coverage.py` |
| Suggest evidence only | Unit: `tests/backend/tools/agentcore-cli/test_docs_suggest_links.py` |
| Doc standards | `agentcore docs-standards` on this file |
| Edges only after sync | Manual / live: apply tokens → sync → explore `DOCUMENTED_BY` |

## Related Documents

- [`03-ingestion-and-living-documentation-workflow.md`](./03-ingestion-and-living-documentation-workflow.md) — Phase 1 / Phase 2 sync.
- [`04-graph-guided-code-generation-workflow.md`](./04-graph-guided-code-generation-workflow.md) — generation context usage.
- [`09-context-pack-retrieval-and-agent-workflow.md`](./09-context-pack-retrieval-and-agent-workflow.md) — context packs.
- [`../agents/TEAM-HANDOUT-agentcore-documentation-complete.md`](../agents/TEAM-HANDOUT-agentcore-documentation-complete.md) — team LIST E hybrid.
- [`../08-software-engineering-architecture/42-agentcore-cli-command-reference-continued-continued-continued.md`](../08-software-engineering-architecture/42-agentcore-cli-command-reference-continued-continued-continued.md) — CLI detail for `docs-suggest-links`.
