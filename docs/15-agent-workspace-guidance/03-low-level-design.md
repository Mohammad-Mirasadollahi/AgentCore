---
doc_id: ac.doc.awg.low-level-design
title: "03 - Agent Workspace Guidance Low-Level Design"
doc_type: low-level-design
status: active
schema_version: "1.0"
owner: platform-architecture
summary: >-
  Artifact model for agents_entry, always_rule, and skill; resolve pipeline;
  token budgets; precedence; and filesystem export layout mapping.
tags:
  - agent-workspace-guidance
  - lld
  - skills
  - rules
  - agents-md
phase: "15-agent-workspace-guidance"
canonical_path: docs/15-agent-workspace-guidance/03-low-level-design.md
related_docs:
  - ac.doc.awg.high-level-design
  - ac.doc.awg.data-contracts
  - ac.doc.common_context.low-level-design
doc_version: "1.0.0"
audience:
  - engineer
  - architect
  - agent
lifecycle_lane: current
concern_lane: architecture
audience_lane:
  - platform-engineering
  - agents
authority: normative
visibility: internal
primary_entities:
  - AgentsEntry
  - AlwaysRule
  - Skill
  - GuidanceExportLayout
relations_declared:
  - type: depends_on
    target: ac.doc.awg.high-level-design
  - type: depends_on
    target: ac.doc.common_context.low-level-design
chunk_hints:
  strategy: heading_h2
  max_tokens: 800
  overlap_tokens: 64
language: en
security_classification: internal
---

# 03 - Agent Workspace Guidance Low-Level Design

## Purpose

This document defines the typed artifact model, resolve pipeline specialization, precedence, token budgets, and filesystem export layouts for Agent Workspace Guidance.

## Typed Guidance Kinds

All kinds are stored as CommonItems with `item_type` (or equivalent discriminant) set to one of the following.

### agents_entry

Project entry document analogous to `AGENTS.md`.

| Field | Requirement |
| --- | --- |
| `title` | Short label (for example `Agent entry`) |
| `body` | Markdown entry: laws, reading order, high-signal skill pointers |
| `status` | Only `approved` items resolve |
| Invariant | At most one **active approved** `agents_entry` per project scope |

### always_rule

Always-on behavioral rule analogous to Cursor `.mdc` with `alwaysApply` (or equivalent).

| Field | Requirement |
| --- | --- |
| `title` | Stable rule name |
| `body` | Rule markdown |
| `applicability` | Optional globs / agent types / workflow types |
| `priority` | Integer; higher wins within same scope when trimming |
| `mandatory` | If true, task override cannot silently drop without conflict record |

### skill

On-demand procedure analogous to `SKILL.md`.

| Field | Requirement |
| --- | --- |
| `name` | Stable slug (unique per project scope) |
| `description` | One-line when-to-use summary for catalog |
| `body` | Full skill markdown (when / how / do-not) |
| `when_to_use` | Structured triggers (keywords, task types, globs) optional |
| Catalog mode | Resolve returns descriptor only; body via get-skill |

## Example Bodies

### Sample agents_entry body

```markdown
# Agent entry

**Law:** reply language and docs standards as linked skills/rules.

## High-signal skills

| Skill | Use when |
| --- | --- |
| `persian-chat-reply` | User writes Persian |
| `api-contract-check` | Changing public APIs |
```

### Sample always_rule body

```markdown
# Reply language law

- Persian chat → Persian reply.
- Committed docs and code identifiers stay English.
```

### Sample skill body

```markdown
---
name: api-contract-check
description: Validate public API changes against naming and DTO standards.
---

# API contract check

## When

- Editing OpenAPI, DTOs, or public REST paths.

## How

1. Read API naming standard docs.
2. Diff request/response schemas.
3. Refuse undocumented breaking changes.
```

## Resolve Pipeline

Guidance resolve reuses the Common Context resolution algorithm with these specializations:

1. Normalize task / session metadata (agent type = coding IDE or autonomous coder).
2. Load approved items for project (+ allowed project groups).
3. Filter to kinds `agents_entry`, `always_rule`, `skill` (plus optional non-typed common items only if profile `include_general_common_context` is true — default **false** for pure guidance resolve).
4. Select at most one `agents_entry` (project wins over org fallback).
5. Evaluate applicability for `always_rule` and include until always-on budget is exhausted (sort by mandatory, priority, reuse score, token efficiency).
6. Build **skill catalog** from applicable skills (name, description, when_to_use, id, version) without bodies, until catalog budget is exhausted.
7. Apply precedence against explicit task overrides; record conflicts.
8. Persist audit; return bundle.

### Precedence

1. Explicit authorized task instructions (highest).
2. Project-scoped guidance items.
3. Project-group shared guidance.
4. Organization default templates (lowest), unless `mandatory` governance.

Mandatory items that conflict with task overrides produce a visible conflict and follow safety policy (block vs warn) from feature profile.

## Token Budgets

| Budget slice | Default intent |
| --- | --- |
| `entry_budget` | Fit full entry or summarized variant |
| `always_rules_budget` | Cap always-on injection |
| `skill_catalog_budget` | Descriptors only |
| `skill_body_budget` | Per get-skill call |

Long rule/skill bodies should support a `summary_body` field for budget trimming while keeping full text fetchable.

## Get Skill Behavior

1. Validate skill id belongs to resolved project scope and is approved.
2. Re-check applicability optional (profile flag).
3. Return body + version + hash.
4. Record `SkillFetched` effectiveness signal linked to `bundle_id` when provided.

## Export Layout Mapping

Layout profiles map typed items to paths under a configured workspace root.

### Layout `cursor`

| Kind | Path pattern |
| --- | --- |
| `agents_entry` | `AGENTS.md` |
| `always_rule` | `.cursor/rules/<slug>.mdc` |
| `skill` | `.cursor/skills/<name>/SKILL.md` and/or `.agents/skills/<name>/SKILL.md` |

Frontmatter for `.mdc` export should set always-apply semantics when the item is `always_rule`.

### Layout `claude_compatible`

| Kind | Path pattern |
| --- | --- |
| `agents_entry` | `AGENTS.md` (and optional `CLAUDE.md` alias if profile enables dual write) |
| `always_rule` | Project rules directory as configured by layout profile |
| `skill` | Skills directory with `SKILL.md` per name |

Exact Claude path aliases are layout-profile configuration, not hard-coded product law. The portable contract is the typed Common Context model plus MCP resolve.

### Layout `generic_agents_md`

Only writes `AGENTS.md` embedding a generated index of rules and skill names for minimal clients.

## Materialize Conflict Rules

| Disk state | Action |
| --- | --- |
| Missing | Write managed file; record hash |
| Exists, managed, hash matches last export | Rewrite from SoT |
| Exists, managed, local hash differs | Conflict unless `force_overwrite_managed=true` |
| Exists, unmanaged (no export record) | Conflict; never silent overwrite |
| SoT item retired | Delete only if managed and profile `delete_retired_exports=true`; else leave and report |

## Testing Requirements

- Invariant: two approved `agents_entry` in one project → resolve error or deterministic winner with conflict (prefer reject-on-create).
- Budget trim drops lowest priority non-mandatory rules first.
- Skill catalog never includes raw bodies.
- Export dry-run returns the same conflict set as apply without writes.
- Precedence cases covered by unit tests with fixed fingerprints.
