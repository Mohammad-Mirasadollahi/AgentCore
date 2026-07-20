---
doc_id: ac.doc.awg.mcp-first-skills-rules
title: "06 - MCP-First Agent Skills And Rules"
doc_type: feature-specification
status: active
schema_version: "1.0"
owner: platform-product
summary: >-
  Normative always-on rule and on-demand skills that instruct Cursor and other
  coding agents to route AgentCore-capable work through MCP tools instead of
  inventing local-only substitutes.
tags:
  - agent-workspace-guidance
  - mcp
  - skills
  - rules
  - cursor
  - coding-agents
phase: "15-agent-workspace-guidance"
canonical_path: docs/15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md
related_docs:
  - ac.doc.awg.index
  - ac.doc.awg.feature-specification
  - ac.doc.awg.data-contracts
  - ac.doc.sea.usage-profile-cursor-mcp
doc_version: "1.0.0"
audience:
  - engineer
  - architect
  - product
  - agent
lifecycle_lane: current
concern_lane: feature
audience_lane:
  - platform-engineering
  - agents
  - product
authority: normative
visibility: internal
primary_entities:
  - AlwaysRule
  - Skill
  - AgentWorkspaceGuidanceBundle
  - UsageProfile
relations_declared:
  - type: complements
    target: ac.doc.awg.feature-specification
  - type: depends_on
    target: ac.doc.awg.data-contracts
chunk_hints:
  strategy: heading_h2
  max_tokens: 800
  overlap_tokens: 64
language: en
security_classification: internal
---

# 06 - MCP-First Agent Skills And Rules

## Purpose

This document specifies the **platform-seeded** always-on rule and on-demand skills that coding agents (Cursor, Claude Code–style clients, and other MCP clients) must follow so that work AgentCore can perform is requested **through MCP** against AgentCore—not reinvented with ad-hoc local scripts, unmanaged chat-only notes, or bypass of governed stores.

These artifacts are first-class `always_rule` / `skill` / `agents_entry` content under Agent Workspace Guidance. They ship as a default seed pack for Usage Profiles such as `programming-cursor-mcp` and may be exported to IDE-native paths.

## Problem Statement

MCP tools alone are insufficient: agents often ignore them unless rules and skills tell them *when* and *how* to call AgentCore. Without explicit MCP-first guidance, agents:

- search the repo blindly instead of using the code graph;
- keep facts only in chat instead of memory / durable writes;
- skip docs-sync drift and coverage checks;
- never resolve project guidance before coding.

## Goals

- Define one mandatory always-on rule: prefer AgentCore MCP for in-scope capabilities.
- Define a skill catalog aligned to AgentCore capability areas and current/planned MCP tools.
- Require connect-time `agentcore_guidance_resolve` (when available) before substantive coding.
- Keep skill bodies portable across Cursor and other MCP coding agents (same when/how structure).
- Seed these artifacts from the platform so new projects do not start empty.

## Non-Goals

- Not implementing MCP handlers in this document (contracts remain in [`04-data-contracts-and-events.md`](04-data-contracts-and-events.md) and Usage Profile catalogs).
- Not replacing IDE-local rules used while developing the AgentCore monorepo (`docs/agents/`).
- Not requiring every AgentCore HTTP API to have an MCP twin on day one; skills may say “use MCP if listed on effective profile, else report gap”.

## Always-On Rule: `mcp-first-agentcore`

| Field | Value |
| --- | --- |
| Kind | `always_rule` |
| `name` / slug | `mcp-first-agentcore` |
| `mandatory` | `true` for profiles that enable AgentCore MCP |
| Export (Cursor) | `.cursor/rules/mcp-first-agentcore.mdc` with always-apply |

### Normative body

```markdown
# MCP-first AgentCore

When this workspace is connected to AgentCore over MCP:

1. Call `agentcore_guidance_resolve` (if available on `tools/list`) before substantive coding.
2. For capabilities AgentCore exposes on the active Usage Profile, prefer the matching MCP tool over inventing a local-only substitute.
3. Do not store project facts only in chat when `agentcore_write` or `agentcore_memory_retrieve` can persist or recall them.
4. Do not skip code-graph search when locating symbols AgentCore can index.
5. Do not skip docs-sync tools when checking drift, coverage, or drafting docs AgentCore governs.
6. If a needed capability is missing from `tools/list`, call `agentcore_get_effective_profile` (if available), report the gap, and ask before bypassing with unmanaged workflows.
7. Keep identifiers, paths, and committed docs in English; follow any other always-on project rules from the guidance bundle.
```

## Agents Entry Pointers

The project `agents_entry` body **must** list high-signal MCP skills (at minimum the seed catalog below) so agents discover them after resolve/export.

```markdown
# Agent entry

**Law:** MCP-first AgentCore (always-on rule `mcp-first-agentcore`).

## Session start

1. Resolve workspace guidance via MCP when tools are available.
2. Follow always-on rules from the bundle.
3. Open the matching skill before large memory, graph, docs, or durable-write work.

## High-signal skills

| Skill | Use when |
| --- | --- |
| `agentcore-session-bootstrap` | Starting a coding session on an AgentCore-connected project |
| `agentcore-memory` | Need prior decisions, facts, or task context from AgentCore |
| `agentcore-code-graph` | Finding symbols, call paths, or ownership via the code graph |
| `agentcore-durable-write` | Persisting memory, task, activity, or decision records |
| `agentcore-docs-sync` | Docs drift, coverage, validate, note, draft, or index |
| `agentcore-create-task` | Creating a durable follow-up Task in AgentCore |
```

## Skill Catalog

Each skill is a Common Context `skill` item. Bodies below are normative seed text (English). Tool names are stable MCP names; if a profile omits a tool, the skill must fail closed or report the gap per the always-on rule.

### Skill matrix

| Skill `name` | AgentCore capability | Primary MCP tools | When to use |
| --- | --- | --- | --- |
| `agentcore-session-bootstrap` | Connect / guidance / profile | `agentcore_ping`, `agentcore_get_effective_profile`, `agentcore_guidance_resolve`, `agentcore_guidance_list_skills`, `agentcore_guidance_get_skill` | Session start; before first substantive edit |
| `agentcore-memory` | Memory retrieve / recall | `agentcore_memory_retrieve`; optional write via `agentcore_write` (`resource=memory`) | Need prior facts, decisions, or task context |
| `agentcore-code-graph` | Code knowledge graph | `agentcore_code_graph_explore` (primary), hybrid search, detect_changes, architecture/path | Locate symbols, flows, review impact, and architecture before wide filesystem search |
| `agentcore-durable-write` | Durable project records | `agentcore_write` | Persist memory, task, activity, or decision |
| `agentcore-docs-sync` | Docs-as-code sync | `agentcore_docs_drift_check`, `agentcore_docs_write`, `agentcore_docs_status` | Drift, coverage, validate, note, draft, index |
| `agentcore-create-task` | Core data Task | `agentcore_create_task` (or `agentcore_write` with `resource=task`) | Explicit durable follow-up work |

Guidance tools (`agentcore_guidance_*`) are specified in phase 15 contracts; other tools match the `programming-cursor-mcp` catalog (and successors).

### Skill body: `agentcore-session-bootstrap`

```markdown
---
name: agentcore-session-bootstrap
description: Bootstrap an AgentCore MCP session—ping, profile, resolve guidance, then code.
---

# AgentCore session bootstrap

## When

- Starting work on a project connected to AgentCore via MCP.
- After MCP reload or Usage Profile change.

## How

1. Call `agentcore_ping` to confirm connectivity.
2. Call `agentcore_get_effective_profile` to see allowed MCP tools.
3. If `agentcore_guidance_resolve` is listed, call it and apply `agents_entry` + `always_rules`.
4. If a catalog skill matches the user task, call `agentcore_guidance_get_skill` before improvising.
5. Only then start memory/graph/docs/write tools or local edits.

## Do not

- Start large refactors before guidance resolve when the tool is available.
- Assume tools exist without checking the effective profile / `tools/list`.
```

### Skill body: `agentcore-memory`

```markdown
---
name: agentcore-memory
description: Retrieve or persist project memory through AgentCore MCP.
---

# AgentCore memory

## When

- Need prior decisions, conventions, or facts for this project.
- User asks to remember or recall something durable.

## How

1. Retrieve with `agentcore_memory_retrieve` (`query`, optional `include_history`).
2. To persist a new fact, use `agentcore_write` with `resource=memory` (`title`, `body`, optional `tags`, `confidence`).
3. Cite what AgentCore returned; do not silently invent memory.

## Do not

- Keep durable project facts only in chat when write/retrieve tools are available.
```

### Skill body: `agentcore-code-graph`

```markdown
---
name: agentcore-code-graph
description: Search AgentCore code knowledge graph before wide local search.
---

# AgentCore code graph

## When

- Locating symbols, owners, callers, or related modules for a coding task.
- Planning a change and needing graph-guided context.

## How

1. Prefer `agentcore_code_graph_explore` for "how does X work", flows, or surveying an area (one call: seeds + call path + budgeted source).
2. Use `agentcore_code_graph_hybrid_search` or `agentcore_code_graph_search` for name/meaning lookup when you only need ids.
3. For reviews/PRs call `agentcore_code_graph_detect_changes` with changed file paths.
4. For architecture questions use `agentcore_code_graph_architecture_overview` or `agentcore_code_graph_path`.
5. Escalate to Read/`rg` only for pending-sync banners, low-confidence edges, or empty graph; report degraded mode when tools fail.

## Do not

- Prefer exhaustive workspace crawl when graph explore/search is available and healthy.
- Re-verify explore results with wide Grep when the pack already returned verbatim source.
```

### Skill body: `agentcore-durable-write`

```markdown
---
name: agentcore-durable-write
description: Write memory, task, activity, or decision records via AgentCore MCP.
---

# AgentCore durable write

## When

- Persisting a decision, activity note, memory, or task the project should retain.

## How

1. Call `agentcore_write` with `resource` in `memory` | `task` | `activity` | `decision`.
2. Fill the fields required for that resource (`title`/`body`/`instructions`/`summary` as applicable).
3. Confirm the tool result ids to the user when useful.

## Do not

- Fake success if the tool fails; surface the error and ask how to proceed.
```

### Skill body: `agentcore-docs-sync`

```markdown
---
name: agentcore-docs-sync
description: Run AgentCore docs-sync drift, status, validate, note, draft, and index via MCP.
---

# AgentCore docs sync

## When

- Checking documentation drift or coverage.
- Validating frontmatter, indexing a note, or drafting docs for a symbol.

## How

1. Coverage / gaps: `agentcore_docs_status`.
2. Drift for a symbol: `agentcore_docs_drift_check` (`symbol`, optional `file_path`).
3. Write workflows: `agentcore_docs_write` with `mode` in `validate` | `note` | `draft` | `index` and required fields for that mode.
4. Keep committed documentation English per project laws.

## Do not

- Bypass docs-sync for governed doc changes when these tools are on the profile.
```

### Skill body: `agentcore-create-task`

```markdown
---
name: agentcore-create-task
description: Create a durable AgentCore Task for follow-up engineering work.
---

# AgentCore create task

## When

- User or plan needs a durable follow-up Task tracked in AgentCore.

## How

1. Prefer `agentcore_create_task` with `title` and optional `instructions`.
2. Alternatively `agentcore_write` with `resource=task` when that path is required by profile docs.
3. Return the created task identity from the tool result.

## Do not

- Treat ephemeral chat checklists as a substitute for durable Tasks when the user asked to track work in AgentCore.
```

## Seed Pack And Delivery

| Mechanism | Requirement |
| --- | --- |
| Platform seed | Default Common Context items for programming Usage Profiles (approved or auto-approve policy per org) |
| MCP resolve | Included in `agentcore_guidance_resolve` for coding agent type |
| Filesystem export | Rule → always-apply `.mdc`; skills → `SKILL.md` trees; entry → `AGENTS.md` |
| Profile gate | Skills that reference tools not on `tools/list` still ship; bodies require gap reporting |

Suggested seed pack id: `awg-seed-mcp-first-programming`.

## Product Workflow For Coding Agents

```text
MCP connect
  → agentcore-session-bootstrap skill (ping, profile, guidance_resolve)
  → apply always_rule mcp-first-agentcore
  → pick capability skill (memory | code-graph | docs-sync | durable-write | create-task)
  → call matching MCP tool(s)
  → then local code edits as needed
```

## Interaction With Usage Profiles

- `programming-cursor-mcp` (and successors) **should** advertise the tools referenced above as they are implemented.
- When guidance MCP tools are not yet implemented, seed skills still document the intended names; session bootstrap degrades to ping + effective profile until guidance tools ship.
- Adding a new AgentCore MCP capability requires: tool catalog entry, skill (or always-on update), agents_entry row, and contract tests.

## Acceptance Criteria

- Seed pack defines `mcp-first-agentcore` plus the six skills in the matrix.
- Exported Cursor layout yields always-apply rule + skill folders an agent can load.
- Feature/product docs state that coding agents must route in-scope work through MCP per this document.
- New MCP tools cannot ship in a programming profile without an owning skill or an explicit always-on clause update.

## Open Gaps

| Gap | Notes |
| --- | --- |
| Guidance MCP tools not yet in `programming-cursor-mcp.json` | Specified in phase 15 contracts; add at implementation |
| Hard enforcement of “resolve before write” | Soft via this rule/skill; optional gateway gate later |
| Non-Cursor agents | Same skill/rule bodies; layout profile maps paths |
