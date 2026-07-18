---
doc_id: ac.doc.master.documentation-structure-machine-ingest
title: "08 - Documentation Structure And Machine Ingest Standard"
doc_type: standard
status: active
schema_version: "1.0"
owner: platform-docs
summary: >-
  Normative authoring rules for AgentCore documentation: modular small files,
  tree layout, numbering, titles, YAML frontmatter, RAG/LLMIndex chunking,
  GraphRAG links, and fallback ingest.
tags:
  - documentation
  - rag
  - llmindex
  - graphrag
  - authoring
  - frontmatter
phase: "00-master-plan"
canonical_path: docs/00-master-plan/08-documentation-structure-and-machine-ingest-standard.md
related_docs:
  - ac.doc.master.professional-documentation
doc_version: "1.0.0"
audience:
  - engineer
  - architect
  - agent
primary_entities:
  - DocumentationStructure
  - IngestTier
  - DocChunk
relations_declared:
  - type: complements
    target: ac.doc.master.professional-documentation
  - type: depends_on
    target: docs/03-docs-as-code-sync/
chunk_hints:
  strategy: heading_h2
  max_tokens: 800
  overlap_tokens: 64
language: en
security_classification: internal
---

# 08 - Documentation Structure And Machine Ingest Standard

## Purpose

This document is the normative **authoring and structure** standard for AgentCore documentation. It defines how humans and agents must name files, number folders, write titles and headings, attach metadata, cross-link entities, and shape prose so documentation is:

1. **Modular** — many focused files beat one mega-document; size stays bounded so humans and agents load only what they need.
2. **Discoverable** — indexes, stable IDs, and predictable paths find the right doc fast.
3. **Chunkable** — RAG, LLMIndex, and similar embedders split text at safe boundaries without losing meaning.
4. **Graph-linkable** — GraphRAG and the docs knowledge graph can attach nodes and edges without guessing.
5. **Fallback-safe** — missing or invalid machine metadata never makes a document unreadable to humans or to a plain Markdown reader.

This standard complements, and does not replace:

| Document | Owns |
| --- | --- |
| `06-professional-documentation-standard.md` | Audience, tone, required *content* sections, acceptance quality |
| `../03-docs-as-code-sync/` and `../06-technical-logic/03-docs-sync-technical-logic.md` | Indexing pipelines, AST anchors, drift detection, CI gates |
| `../08-software-engineering-architecture/22-product-design-and-engineering-specification-discipline.md` | Dual-track product + engineering specification discipline |

Authors **must** follow this document when creating or materially revising any Markdown under `docs/`, service `docs/`, runbooks, and ADRs that participate in product knowledge.

## Design Goals

| Goal | Requirement |
| --- | --- |
| Modular by default | One concern per file; prefer a new numbered sibling over growing an existing file past size budgets |
| One tree, one grammar | Phase folders, zero-padded file numbers, and H1/H2 shapes stay consistent across the tree |
| Machine-first metadata, human-first body | YAML frontmatter routes; Markdown body explains |
| Stable identity over path | `doc_id` and heading anchors survive renames better than raw paths alone |
| Optimal retrieval | Chunks are self-describing; sections answer one question; retrieval pulls few small files, not a wall of prose |
| Graceful degradation | Tiered ingest: full metadata → partial → body-only heuristics → raw Markdown |

## Non-Goals

- Replacing product feature specs with a second parallel doc set.
- Requiring every historical file to be rewritten in one pass (migrate opportunistically; new docs must comply).
- Mandating a specific commercial RAG vendor.
- Putting Persian (or any non-English) into committed documentation bodies.
- Writing “complete encyclopedia” single files that mix HLD, LLD, runbook, API catalog, and examples in one body.

---

## 1. Tree Layout And Numbering

### 1.1 Top-level phase folders

Product documentation lives under `docs/` in **zero-padded, numbered phase folders**:

```text
docs/
  NN-kebab-topic/
    00-index.md
    NN-kebab-topic.md
```

Rules:

- Folder prefix `NN` is two digits (`00` … `99`), then a kebab-case topic slug.
- Each phase folder **must** contain `00-index.md` as the local entry point.
- Phase numbers are assigned in the master reading order; do not reuse a retired number for a different topic.
- New cross-cutting standards may use a new top-level `NN-…` folder (example: `14-api-design-and-naming-standards/`) instead of stuffing unrelated files into an existing phase.

### 1.2 File numbering inside a folder

| Pattern | Meaning |
| --- | --- |
| `00-index.md` | Folder map, purpose, file list, reading order |
| `01-…`, `02-…`, … | Ordered content files |
| Suffix `-HLD.md`, `-LLD.md`, `-service-design.md` | Allowed type markers after the number and slug |

Rules:

- Use **two-digit** prefixes (`01`, `02`, …). Prefer contiguous numbers; gaps are allowed only when a reserved slot is documented in the folder index.
- Filename slug is **kebab-case ASCII**, max ~80 characters, no spaces.
- Do not encode version in the filename (`-v2`); use frontmatter `schema_version` / `doc_version` and `supersedes`.
- One primary topic per file. Split oversized documents; do not bury a second topic under a misleading title. See §1.4.

### 1.3 Canonical path identity

For citations and indexes, the **canonical path** is repo-relative from the repository root, forward slashes only:

```text
docs/00-master-plan/08-documentation-structure-and-machine-ingest-standard.md
```

Indexes (`docs/README.md`, folder `00-index.md`) **must** list every normative file in that folder.

### 1.4 Modular files And Size Budgets (normative)

**Principle:** documentation volume is controlled by **splitting into modules**, not by stuffing more sections into one file. A thin `00-index.md` plus several focused siblings is the default shape for every phase folder.

| Rule | Requirement |
| --- | --- |
| One concern per file | Feature spec, HLD, LLD, contracts, risks, runbook, and examples are **separate files** when the topic is non-trivial (mirror `03-docs-as-code-sync/` and `14-api-design-and-naming-standards/`) |
| Soft size budget | Target **≤ ~400 lines** of body Markdown per content file (excluding frontmatter). Crossing ~400 is a signal to split |
| Hard size budget | New or materially revised normative files **must not** exceed **~800 lines** of body without an explicit split plan in the folder index |
| Section budget | Prefer **≤ ~12 H2 sections** per file; more H2s usually means a second file |
| No duplication | Shared facts live in one canonical file; others link with one-line context |
| Index stays thin | `00-index.md` maps and orders; it must not become a second full design doc |
| Split, do not append | When adding a large new capability, create `NN-new-topic.md` (or a subfolder with its own `00-index.md`) instead of growing an unrelated sibling |

**When to split immediately**

- Two audiences need different depth (operator runbook vs engineer LLD).
- Two lifecycles diverge (stable contract vs evolving examples).
- A single H2 subsection is becoming a mini-document (> ~80–100 lines).
- RAG/context packs would pull mostly irrelevant neighbors from the same file.

**How to split**

1. Keep a stable `doc_id` on the canonical file that still owns the core topic; give each new file its own `doc_id`.
2. Move whole H2 sections (not half-paragraphs) into the new file.
3. Leave a short stub H2 or Related Documents entry pointing to the new path/`doc_id`.
4. Update the folder `00-index.md` and any reading-order lists.
5. Declare `relations_declared` / `related_docs` between the siblings (`complements` or `depends_on`).

**Anti-patterns**

- One “phase bible” Markdown that mixes every design depth.
- Copy-pasting the same API table into five files.
- Deep folder trees of one-line stubs with no real ownership (prefer a sibling file in the same phase).
- Inflating `summary` or Purpose with content that belongs in a dedicated sibling.

Modularity improves retrieval: agents and RAG load **only the relevant module**, keep citation precision high, and avoid token waste from mega-files.

---

## 2. Titles And Heading Grammar

### 2.1 Document title (H1)

- Exactly **one** H1 per file.
- H1 form: `# NN - Title In Title Case` when the file is numbered, or `# Title In Title Case` for unnumbered service READMEs.
- H1 **must** match frontmatter `title` when frontmatter is present (same words; punctuation may differ only by trailing period).
- Do not put the full folder path in the H1.

### 2.2 Section headings (H2+)

| Level | Use |
| --- | --- |
| H2 (`##`) | Primary sections; preferred **chunk boundaries** for RAG |
| H3 (`###`) | Subsections inside one chunkable topic |
| H4+ | Rare; prefer lists/tables over deep nesting |

Rules:

- Heading text is **sentence-style Title Case or short noun phrases** — stable, searchable, unique within the file.
- Prefer headings that stand alone as retrieval queries, e.g. `## Drift Detection Algorithm`, not `## Details`.
- Do not number headings manually (`## 3.2 Foo`) unless the number is part of a stable public clause ID (see §3.3). Prefer unnumbered headings; file numbering carries order.
- Do not skip levels (H2 → H4).
- Avoid emoji, marketing adjectives, and vague headings (`Overview`, `Notes`, `Misc`) unless followed by a specific qualifier (`## Overview Of Ingest Tiers`).

### 2.3 Heading anchors

Authors should assume GitHub-style / CommonMark slug anchors:

- Lowercase, spaces → `-`, strip most punctuation.
- Prefer heading text that yields a short, unique slug.
- When linking to a section, use relative links with explicit fragments:

```markdown
See [Fallback Tiers](./08-documentation-structure-and-machine-ingest-standard.md#7-fallback-tiers-and-graceful-degradation).
```

If two headings would collide, disambiguate the heading text rather than relying on auto-suffixes.

### 2.4 Opening paragraph after H1

Immediately after the H1 (and optional frontmatter), place a **Purpose** (or equivalent) H2 whose first paragraph states:

- what the document owns,
- who uses it,
- what it does **not** own (pointer to sibling docs).

This paragraph is the preferred **document-level summary** for indexes and LLMIndex document nodes.

---

## 3. Stable Identifiers

### 3.1 `doc_id`

Format (normative):

```text
ac.doc.<domain>.<slug>
```

Examples:

```text
ac.doc.master.documentation-structure-machine-ingest
ac.doc.memory.dynamic-context-rag
ac.doc.docs_sync.feature-specification
```

Rules:

- `doc_id` is **immutable** after first publish. Renaming a file does not change `doc_id`.
- Use lowercase ASCII, digits, dots, and hyphens only.
- Domain segment mirrors the phase or bounded context (`master`, `memory`, `docs_sync`, `api`, `ops`, …).
- Never reuse a retired `doc_id`; mark `status: archived` and point successors with `supersedes` / `superseded_by`.

### 3.2 Entity references in body

When referring to system entities, prefer stable tokens that indexers can extract:

| Entity | Pattern in prose / lists |
| --- | --- |
| Document | `doc_id` or relative Markdown link |
| Code symbol | `linked_symbols` entry / `` `path::Symbol` `` |
| Decision | `DEC-YYYY-NNN` or ADR path |
| Issue / Task | tracker id as used by the platform |
| API route | `` `METHOD /api/v1/...` `` |
| Config key | `` `ENV_OR_KEY_NAME` `` |
| Service | kebab service name as in architecture docs |

### 3.3 Optional clause IDs

For normative requirements that must be cited in tests or ADRs, authors **may** tag a short clause after a heading or bullet:

```markdown
## Frontmatter Required Fields

- **[DOC-INGEST-REQ-001]** Every new normative doc under `docs/` must include valid frontmatter at ingest tier Full.
```

Clause IDs are uppercase, hyphen-separated, stable, and listed once. Do not renumber casually.

---

## 4. YAML Frontmatter Schema

### 4.1 Placement

Frontmatter is a YAML block at the **very start** of the file, enclosed by `---` lines. The H1 follows the closing `---`.

Documents without frontmatter remain **human-readable** (Fallback Tier Body / Raw). They **must not** be treated as synchronized technical documentation by docs-sync (see technical logic).

### 4.2 Required fields (ingest tier Full)

```yaml
---
doc_id: ac.doc.master.documentation-structure-machine-ingest
title: "08 - Documentation Structure And Machine Ingest Standard"
doc_type: standard
status: active
schema_version: "1.0"
owner: platform-docs
summary: >-
  Normative authoring rules for tree layout, numbering, titles, frontmatter,
  RAG chunking, GraphRAG links, and fallback ingest.
tags:
  - documentation
  - rag
  - graphrag
  - authoring
phase: "00-master-plan"
canonical_path: docs/00-master-plan/08-documentation-structure-and-machine-ingest-standard.md
---
```

| Field | Type | Rules |
| --- | --- | --- |
| `doc_id` | string | See §3.1 |
| `title` | string | Matches H1 |
| `doc_type` | enum | See §4.4 |
| `status` | enum | `draft` \| `active` \| `deprecated` \| `archived` |
| `schema_version` | string | Semver of **this frontmatter schema**, not product version |
| `owner` | string | Team or role slug |
| `summary` | string | 1–3 sentences; used as embedding preamble / card text |
| `tags` | string[] | Lowercase kebab; 3–12 items |
| `phase` | string | Folder name or `service:<name>` / `adr` / `runbook` |
| `canonical_path` | string | Repo-relative path |

### 4.3 Recommended fields (enrich GraphRAG / filters)

```yaml
linked_symbols: []          # code symbols this doc explains
decision_refs: []           # DEC-… / ADR paths
related_docs:               # doc_id list
  - ac.doc.master.professional-documentation
related_issues: []
supersedes: null            # prior doc_id
superseded_by: null
reviewed_by: null
reviewed_at: null           # ISO-8601 date
doc_version: "1.0.0"        # document revision
audience:
  - engineer
  - architect
  - agent
primary_entities:           # ubiquitous language nouns for graph nodes
  - DocumentationStructure
  - IngestTier
  - DocChunk
relations_declared:         # author-declared edges (hint for GraphRAG)
  - type: complements
    target: ac.doc.master.professional-documentation
  - type: implemented_by
    target: docs-sync-service
chunk_hints:
  strategy: heading_h2
  max_tokens: 800
  overlap_tokens: 64
language: en
security_classification: internal
```

### 4.4 `doc_type` values

| Value | Use |
| --- | --- |
| `index` | Folder `00-index.md` |
| `standard` | Normative rules |
| `hld` | High-level design |
| `lld` | Low-level design |
| `feature_spec` | Feature specification |
| `service_design` | Full service design |
| `runbook` | Operational procedure |
| `adr` | Architecture decision |
| `contract` | API / event / schema contract narrative |
| `example` | Logical implementation example |
| `gap` | Gap analysis |
| `glossary` | Glossary / ubiquitous language |
| `readme` | Local README |

### 4.5 Validation failures (machine)

Invalid frontmatter ⇒ emit validation finding, **exclude from sync / Full ingest**, still allow Fallback tiers. Do not delete or rewrite body automatically.

---

## 5. Body Structure For RAG And LLMIndex

### 5.1 Chunking contract

Default chunk strategy for AgentCore docs:

1. Split on **H2** boundaries.
2. Keep H3+ with their parent H2 when under `chunk_hints.max_tokens`.
3. Prepend to each chunk a **machine preamble** built by the indexer (not necessarily written twice by the author):

```text
doc_id: …
title: …
section: <H2 text>
canonical_path: …
tags: …
```

Authors help the indexer by:

- Keeping each H2 section focused on **one** concern.
- Starting each H2 with a short definitional paragraph (2–4 sentences) before tables or lists.
- Preferring tables for structured facts (fields, states, APIs).
- Putting long code samples in fenced blocks immediately after the prose that explains them.
- Avoiding “continued below” without a heading break.

### 5.2 Self-contained sections

A retrieved chunk must remain understandable without the previous section. Therefore:

- Restate the entity name in the first sentence of an H2 when the heading alone is ambiguous.
- Do not rely on “as above” for normative rules; link or restate the rule id.
- Put prerequisites in a `## Dependencies` / `## Related Documents` section rather than implied narrative order only.

### 5.3 Summary and TL;DR patterns

- Frontmatter `summary` = document-level card.
- Optional `## Summary` H2 near the top for human skimming; keep it aligned with `summary`.
- Do not invent conflicting abstracts in the middle of the file.

### 5.4 Code and path citations

- Use fenced code blocks with a language tag (` ```python `, ` ```yaml `, ` ```text `).
- Cite repository paths in backticks: `` `backend/services/docs-sync-service/` ``.
- Prefer stable symbol paths over line numbers in prose.

### 5.5 Lists and tables

- Use tables for contracts, enums, state models, and field dictionaries.
- Use bullet lists for unordered requirements; numbered lists for algorithms and ordered procedures.
- Keep table cells short; move long prose to a following paragraph.

### 5.6 Token hygiene

- Prefer precise short sentences over filler.
- Deduplicate: one canonical section; elsewhere link.
- Avoid pasting large OpenAPI dumps; link to contract packages instead.
- Images need alt text that states the diagram’s claim in one sentence.

---

## 6. GraphRAG And Knowledge-Graph Authoring

### 6.1 Node types authors should imply

Through frontmatter and explicit sections, authors should make these nodes easy to extract:

| Node | Source |
| --- | --- |
| `Document` | `doc_id`, `title`, `canonical_path` |
| `Section` | H2 heading + anchor |
| `Entity` | `primary_entities`, glossary terms |
| `Service` / `Module` | ownership sections, path citations |
| `Symbol` | `linked_symbols` |
| `Decision` | `decision_refs` |
| `Requirement` | clause IDs / acceptance criteria bullets |
| `API` | contract tables |
| `RunbookStep` | numbered operational steps |

### 6.2 Edge types authors may declare

Use `relations_declared` and Related Documents sections. Preferred types (align with docs-as-code graph):

| Edge | Meaning |
| --- | --- |
| `explains` | Doc/section explains a symbol or API |
| `complements` | Sibling standard; both needed |
| `depends_on` | Must read target first |
| `implements` | Code/service implements this spec |
| `supersedes` | Replaces older doc |
| `owned_by` | Team ownership |
| `related_to` | Weak link when none of the above fit |

Do not invent undocumented edge types in frontmatter without updating docs-as-code contracts.

### 6.3 Related Documents section (mandatory for normative docs)

Every `standard`, `hld`, `lld`, `feature_spec`, and `service_design` **must** include:

```markdown
## Related Documents

- `doc_id` or relative path — one-line relationship.
```

List only direct relations. Do not dump the whole tree.

### 6.4 Index files as graph hubs

`00-index.md` files are hubs:

- Summarize folder purpose.
- List each file with one-line description.
- State reading order when order matters.
- Link outward to sibling phases when required.

Indexers **should** treat index files as navigation nodes with `doc_type: index` and high outbound degree.

---

## 7. Fallback Tiers And Graceful Degradation

Ingest and retrieval **must** implement these tiers. Authors write for Tier Full; readers and agents still work at lower tiers.

| Tier | Condition | Behavior |
| --- | --- | --- |
| **Full** | Valid frontmatter + parseable Markdown | Sync-eligible; filters by tags/phase/status; H2 chunks with preamble; GraphRAG edges from metadata |
| **Partial** | Frontmatter present but missing recommended fields or unknown extras | Index required fields; ignore unknown keys; warn; still chunk on H2 |
| **Body** | No frontmatter or invalid YAML | Derive `title` from first H1; `doc_id` provisional from `canonical_path` hash; `summary` from first paragraph; **do not** mark synced; still embed and search |
| **Raw** | Markdown parse failure or non-UTF8 repaired | Store opaque text blob; keyword / full-text search only; surface parse error to operators |
| **Link-heal** | Broken relative link | Keep text; record broken-link finding; retrieval still returns the source chunk |
| **Graph-heal** | Missing `linked_symbols` / relations | Use path mentions, inline `` `path::Symbol` ``, and Related Documents links as weak edges; never drop the document |

### 7.1 Hard guarantees

1. **Human readability always wins** — a file that opens in a Markdown viewer and makes sense is never rejected from the repository solely for missing frontmatter.
2. **No silent discard** — failed Full ingest must leave Body/Raw retrieval available.
3. **Provisional IDs are not durable** — Body-tier synthetic ids must be replaced when frontmatter is added; re-key embeddings on upgrade.
4. **Bloom / graph negatives are not proof of absence at Body tier** — fall back to path and full-text search (see docs-sync Bloom fallback rules).

### 7.2 Author migration path

When editing a legacy file:

1. Add Full frontmatter if the file is normative or frequently retrieved.
2. Ensure single H1 and coherent H2 sections.
3. Add Related Documents.
4. Leave prose English and implementation-grade per `06-…`.

---

## 8. Document Templates

### 8.1 Normative standard (skeleton)

```markdown
---
doc_id: ac.doc.<domain>.<slug>
title: "NN - Human Title"
doc_type: standard
status: draft
schema_version: "1.0"
owner: <team>
summary: >-
  One to three sentences.
tags: [documentation]
phase: "<folder>"
canonical_path: docs/<folder>/<file>.md
related_docs: []
chunk_hints:
  strategy: heading_h2
  max_tokens: 800
  overlap_tokens: 64
language: en
---

# NN - Human Title

## Purpose

…

## Scope

…

## Normative Rules

…

## Examples

…

## Related Documents

…

## Acceptance Criteria

…
```

### 8.2 Feature / design docs

Follow section lists in `06-professional-documentation-standard.md`. Additionally:

- Keep each major required section as its **own H2** (maps 1:1 to chunks).
- Put state machines and algorithms under clearly named H2s.
- Put acceptance criteria in a final H2 with verifiable bullets.

### 8.3 Runbook

Required H2s:

- Purpose / Scope
- Symptoms
- Diagnosis
- Remediation Steps (numbered)
- Rollback
- Verification
- Escalation
- Related Documents

### 8.4 Folder index

```markdown
---
doc_id: ac.doc.<domain>.index
title: "NN - <Topic> Index"
doc_type: index
status: active
schema_version: "1.0"
owner: <team>
summary: Entry map for this documentation folder.
tags: [index]
phase: "<folder>"
canonical_path: docs/<folder>/00-index.md
language: en
---

# NN - <Topic> Index

## Purpose

…

## Files

- `01-….md` — …

## Reading Order

1. …
```

---

## 9. Authoring Workflow (Humans And Agents)

1. Read this standard and `06-professional-documentation-standard.md`.
2. Choose the correct folder; prefer a **new modular file** over extending a large sibling (§1.4).
3. Add the next file number; update `00-index.md` and `docs/README.md` when adding a top-level or master-plan file.
4. Copy a template; set immutable `doc_id`.
5. Write Purpose first; then normative sections as H2s; stop and split if size budgets are approached.
6. Declare Related Documents and `relations_declared` / `related_docs`.
7. Add `linked_symbols` when the doc explains code.
8. Self-check with §10 before merge.

Agents generating docs **must** emit Full-tier frontmatter for new normative files and must not invent `doc_id`s that collide with existing ones (search `doc_id:` / indexes first).

---

## 10. Review Checklist

- [ ] Path under the correct numbered folder; listed in folder `00-index.md`.
- [ ] Filename zero-padded + kebab-case.
- [ ] Modular: one concern per file; body within soft/hard size budgets (§1.4); no mega-doc growth.
- [ ] Exactly one H1; matches `title`.
- [ ] H2 sections are unique, specific, and chunk-sized (≤ ~12 H2s preferred).
- [ ] Frontmatter validates for intended ingest tier (Full for new normative docs).
- [ ] `summary` is accurate and non-marketing.
- [ ] Related Documents present; links resolve; no duplicated canonical tables.
- [ ] English only in committed body.
- [ ] No secrets, credentials, or customer data in examples.
- [ ] Complements `06-…` content requirements where applicable.
- [ ] Fallback: body remains readable if frontmatter were stripped.

---

## 11. Indexer And Retriever Expectations (Implementers)

These are requirements on **software** that consumes docs; authors rely on them.

| Concern | Expectation |
| --- | --- |
| LLMIndex / vector index | One parent document node per `doc_id` (or path at Body tier); child nodes per H2 chunk with preamble |
| Metadata filters | Support `phase`, `tags`, `status`, `doc_type`, `owner`, `security_classification` |
| Hybrid search | Vector + keyword on headings, `summary`, and body |
| GraphRAG | Build Document–Section–Entity–Symbol graph from frontmatter + extracted links; merge with code graph when `linked_symbols` present |
| Context pack assembly | Prefer Full-tier chunks; if empty, Body-tier; always include `canonical_path` and section heading in the pack citation |
| Caching | Key embeddings by `doc_id` + content hash (+ section anchor); invalidate on hash change |

---

## 12. Relationship To Existing Tree Conventions

This repository already uses numbered phase folders and `00-index.md` hubs. This standard **ratifies** that practice and adds machine-ingest, RAG, and fallback rules.

Historical files may omit frontmatter until edited. New normative documentation under `docs/00-master-plan/` and new standards folders **must** comply at Full tier.

Service-local docs under `backend/services/*/docs/` **should** use the same frontmatter schema with `phase: service:<service-name>` and paths relative to repo root in `canonical_path`.

---

## 13. Acceptance Criteria

This standard is satisfied when:

- New normative docs use numbered paths, single H1, H2 chunk boundaries, and Full-tier frontmatter.
- Documentation grows as **modular sibling files** under size budgets (§1.4), not as unbounded mega-documents.
- Indexes list new files and state reading order where needed.
- Retrievers can filter and cite by `doc_id`, path, and section heading, and load only relevant modules.
- Graph builders can create at least Document, Section, and weak Related-Document edges without NLP.
- Documents with missing frontmatter remain searchable and human-readable via Fallback tiers.
- Authors have a single checklist (§10) that covers modularity, structure, metadata, RAG shape, and links.
- This document is linked from `00-index.md` and `docs/README.md` reading order beside `06-professional-documentation-standard.md`.

## Related Documents

- `06-professional-documentation-standard.md` — professional content and tone requirements.
- `../03-docs-as-code-sync/00-index.md` — docs knowledge graph, frontmatter validation, drift.
- `../06-technical-logic/03-docs-sync-technical-logic.md` — indexing and CI gate algorithms.
- `../08-software-engineering-architecture/22-product-design-and-engineering-specification-discipline.md` — specification discipline.
- `../14-api-design-and-naming-standards/00-index.md` — API naming parallel for contracts.
- `../../backend/docs/STRUCTURE_STANDARD.md` — backend folder structure (code, not docs prose).
