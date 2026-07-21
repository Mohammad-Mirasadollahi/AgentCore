---
doc_id: ac.doc.ckg.dead-code-cleanup-loop
title: "36 - Dead-Code Candidates And Cleanup Loop"
doc_type: feature-specification
status: active
schema_version: "1.0"
owner: platform-product
summary: >-
  Normative design for graph-backed unused-symbol candidates, MCP contract,
  live-until-proven exclusions, and the closed loop with Workspace Guidance
  and benefit measurement. AgentCore never mutates the repository.
tags:
  - dead-code
  - unused-symbols
  - code-graph
  - mcp
  - cleanup
  - wedge
phase: "07-code-knowledge-graph"
canonical_path: docs/07-code-knowledge-graph/36-dead-code-candidates-and-cleanup-loop.md
related_docs:
  - ac.doc.ckg.index
  - docs/07-code-knowledge-graph/02-neo4j-schema-design.md
  - docs/07-code-knowledge-graph/09-context-pack-retrieval-and-agent-workflow.md
  - ac.doc.awg.mcp-first-skills-rules
  - docs/09-platform-governance-operations/10-impact-reporting-and-benefit-measurement.md
  - docs/00-master-plan/01-product-scope-and-feature-catalog.md
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
  - product
  - agents
authority: normative
visibility: internal
primary_entities:
  - UnusedCandidate
  - DeadCodeCleanupLoop
relations_declared:
  - type: depends_on
    target: docs/07-code-knowledge-graph/02-neo4j-schema-design.md
  - type: complements
    target: ac.doc.awg.mcp-first-skills-rules
  - type: complements
    target: docs/09-platform-governance-operations/10-impact-reporting-and-benefit-measurement.md
chunk_hints:
  strategy: heading_h2
  max_tokens: 800
  overlap_tokens: 64
language: en
security_classification: internal
---

# 36 - Dead-Code Candidates And Cleanup Loop

## Purpose

This document specifies the **dead-code cleanup full loop** for the AgentCore wedge: detect unused candidates from the Code-Knowledge Graph, guide connected coding agents to remove proven-dead predecessors in the same change, and measure cleanup outcomes.

AgentCore is not the executor. External IDE assistants and agent runtimes delete code. AgentCore owns candidates, guidance seed content, freshness signals, and evidence for benefit measurement.

Product positioning: [`../00-master-plan/01-product-scope-and-feature-catalog.md`](../00-master-plan/01-product-scope-and-feature-catalog.md). Guidance seed: [`../15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md`](../15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md). Measurement: [`../09-platform-governance-operations/10-impact-reporting-and-benefit-measurement.md`](../09-platform-governance-operations/10-impact-reporting-and-benefit-measurement.md).

## Professional Audience

Engineers implementing `code-graph-service` and MCP gateway tools; product owners of the programming wedge; authors of Workspace Guidance seed packs.

## Goals

- Define unused candidates with explicit graph edge rules and confidence.
- Scope cleanup to the task neighborhood or symbols touched by a replace — not repo-wide silent mass deletion.
- Expose a stable MCP tool contract for candidates (implementation may follow this design).
- Mark **live-until-proven** cases so agents skip unsafe deletes.
- Close the loop with guidance + measurable KPIs without AgentCore mutating disk.

## Non-Goals

- AgentCore auto-deleting files or rewriting the working tree.
- Claiming perfect unused detection across dynamic languages or string-based registries.
- Marketing unused detection beyond the v1 language matrix ([`10-language-support-policy.md`](10-language-support-policy.md)).
- Replacing IDE linters; this loop is graph-backed and task-scoped for AI coding sessions.

## Closed Loop

```text
Agent replaces or retires behavior
  → Graph unused-candidate query (task neighborhood)
  → Always-on rule + skill instruct agent to prove and delete
  → External agent deletes proven-dead symbols/imports/tests
  → Activity / WorkLog + graph delta feed cleanup KPIs
```

| Layer | AgentCore owns | External agent owns |
| --- | --- | --- |
| Detect | Candidate query, confidence, blockers, freshness | Confirms dynamic/public API before delete |
| Guide | Seed always-on rule + `agentcore-remove-dead-code` skill | Follows rule in the same coding change |
| Act | Never mutates repo | Deletes proven-dead code |
| Measure | KPIs and evidence linkage | Tests / acceptance as quality signals |

## Candidate Definition

### Symbol candidates

A symbol is an **unused candidate** when, within the declared scope and after the latest successful ingest for that project:

1. There is **no inbound** structural edge of type `CALLS` or `IMPORTS` (via `CODE_REL.rel_type`) from another live symbol or file in scope, and
2. The symbol is not itself an entrypoint excluded below, and
3. Confidence is computed from edge completeness and ingest freshness.

Optional file-level candidates: a file whose exported symbols are all unused candidates and that has no inbound `IMPORTS` from other files in scope.

### Scope

| Scope mode | Meaning |
| --- | --- |
| `task_neighborhood` | Symbols/files within N hops of symbols named in the task or last explore pack (default) |
| `changed_symbols` | Symbols replaced, renamed, or superseded in the current agent session / change set |
| `explicit_paths` | Operator- or agent-supplied path prefixes (still not whole-repo by default) |

Default for coding agents: `changed_symbols` union one-hop `task_neighborhood`. Never default to full-repository scan in the programming Usage Profile.

### Edge types consulted

Normative for v1 (see [`02-neo4j-schema-design.md`](02-neo4j-schema-design.md)):

- Inbound absence of `CALLS` and `IMPORTS`.
- Treat `INHERITS_FROM` / `CONTAINS` as structural membership, not proof of use.
- `DOCUMENTED_BY` / living-doc links do **not** count as runtime use.
- Future edges (`TESTED_BY`, framework routes) may raise confidence or mark “tests-only” — see exclusions.

### Freshness

Respect session pending-sync and stale banners already defined for explore / detect_changes. If freshness is `stale` or ingest is pending:

- Return candidates with `freshness` and `confidence` capped.
- Do not claim live indexing.
- Skill body must tell the agent to re-ingest or treat high-impact deletes as uncertain.

## Live-Until-Proven Exclusions

Treat as **live** (do not list as safe-to-delete, or list only with `blockers`) until human or agent proves otherwise:

| Exclusion | Reason |
| --- | --- |
| `__getattr__` / lazy loaders / plugin registries | Dynamic resolution not visible as `CALLS` |
| String route / permission / feature-flag tables | Name referenced as data, not AST call |
| Public HTTP handlers, IAM permission strings, SDK exports | External callers outside the graph |
| Symbols referenced only from tests | Tests count as use; delete tests **with** prod code when both are dead |
| Entrypoints (`__main__`, CLI `main`, framework `app`) | No inbound graph edges by design |
| User-approved `tsoc-defer:` stopgaps | Do not delete the guarded workaround without root-cause fix |
| Low-confidence `CALLS` edges | Schema already warns against high-risk automation on low confidence |

Ambiguous candidates must appear with `confidence: low` and non-empty `blockers`, not as `safe_to_delete: true`.

## MCP Tool Contract (planned)

Tool name: `agentcore_code_graph_unused_candidates`

### Request (normative fields)

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `project_id` | string | yes | Active project scope |
| `scope_mode` | enum | yes | `task_neighborhood` \| `changed_symbols` \| `explicit_paths` |
| `anchor_symbols` | string[] | no | Qualified names or symbol ids |
| `anchor_paths` | string[] | no | Repo-relative paths |
| `max_results` | int | no | Default bounded (e.g. 50) |
| `include_uncertain` | bool | no | Default false |

### Response (normative fields)

```json
{
  "freshness": "ok|pending_sync|stale",
  "scope_mode": "changed_symbols",
  "candidates": [
    {
      "symbol": "pkg.module.OldHelper",
      "path": "src/pkg/module.py",
      "kind": "function",
      "confidence": "high|medium|low",
      "reasons": ["no_inbound_calls", "no_inbound_imports"],
      "blockers": [],
      "safe_to_delete": true
    }
  ],
  "skipped_uncertain": [
    {
      "symbol": "pkg.routes.login",
      "path": "src/pkg/routes.py",
      "confidence": "low",
      "blockers": ["possible_string_registry", "public_http_handler"]
    }
  ]
}
```

Implementation of the handler and CLI is **follow-on** after this contract; Usage Profiles must advertise the tool only when implemented. Until then, the skill requires graph explore + local `rg` proof (same safety bar).

## Agent Workflow (with guidance)

1. After replacing or retiring behavior, call unused-candidates (or explore + reference proof).
2. For each `safe_to_delete` candidate in scope, prove with repo search and non-Python callers (gateway, OpenAPI, frontend, deploy).
3. Delete symbol **and** exclusive tests / re-exports / docs that only described it.
4. Skip `blockers` / uncertain; optionally open a Task for human review.
5. Run the smallest verification that would fail if the delete were wrong.
6. Record cleanup in Activity / WorkLog (paths removed, candidate ids) for KPI instrumentation.

Normative skill text: `agentcore-remove-dead-code` in phase 15 MCP-first seed pack.

## Measurement Hooks

Emit or attach to WorkLog / Activity:

- `dead_code_candidates_surfaced` (count, scope).
- `dead_code_candidates_resolved` (removed after proof).
- `dead_code_candidates_skipped_uncertain`.
- Optional: net unused LOC removed vs LOC added in the same task.

KPI definitions live in impact reporting (`dead_code_candidates_resolved`, `orphaned_symbols_remaining`). Blind deletes without tests/acceptance must not count as positive benefit.

## Risks And Acceptance

| Risk | Mitigation |
| --- | --- |
| False unused via dynamic dispatch | Exclusions + blockers; never auto-delete |
| Stale graph after local edits | Freshness caps; pending-sync banners |
| Agent deletes public API | Public/export/HTTP exclusions |
| Scope creep to whole repo | Default task/changed scope only |

Acceptance for this design:

- [ ] Candidate definition and exclusions are unambiguous for implementers.
- [ ] MCP request/response fields are stable enough for gateway contract tests when implemented.
- [ ] Product docs state AgentCore does not mutate the repo for cleanup.
- [ ] Seed guidance references this loop and the skill name.
- [ ] Impact KPIs name cleanup metrics and instrumentation sources.

## Related Documents

- [`09-context-pack-retrieval-and-agent-workflow.md`](09-context-pack-retrieval-and-agent-workflow.md) — context packs around coding tasks.
- [`02-neo4j-schema-design.md`](02-neo4j-schema-design.md) — `CODE_REL` / `CALLS` / `IMPORTS`.
- [`22-code-intelligence-enhancements-feature-specification.md`](22-code-intelligence-enhancements-feature-specification.md) — explore / change-risk surfaces.
- [`../15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md`](../15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md) — seed rule and skill.
- [`../09-platform-governance-operations/10-impact-reporting-and-benefit-measurement.md`](../09-platform-governance-operations/10-impact-reporting-and-benefit-measurement.md) — cleanup KPIs.
