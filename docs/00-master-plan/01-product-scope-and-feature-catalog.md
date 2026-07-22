---
doc_id: ac.doc.master.product-scope-and-feature-catalog
title: Product Scope and Feature Catalog
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-docs
summary: AgentCore connects to a codebase and improves the outputs of connected AI coding
  tools.
tags:
- standard
- master
phase: 00-master-plan
canonical_path: docs/00-master-plan/01-product-scope-and-feature-catalog.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols: []
---

# Product Scope and Feature Catalog


## Purpose

AgentCore connects to a codebase and improves the outputs of connected AI coding tools.

## Vision

AgentCore connects to a codebase and improves the outputs of connected AI coding tools.

It indexes repository structure, documentation, decisions, and current project truth, then injects only the relevant context into IDE assistants, agent runtimes, and review workflows. The measurable result is better code and answers: fewer hallucinations, less rework, lower token cost, and clearer impact awareness.

AgentCore is not an agent, an LLM, a coding IDE, or a replacement for agent frameworks. Connected runtimes still write the code. AgentCore owns the code-linked knowledge layer that makes those runtimes produce better work.

## Product Positioning

### Wedge product (delivery focus)

The first product users must understand and adopt is:

**Connect a repository → build structured code knowledge → improve AI outputs on that repository.**

**v1 feature sentence (frozen 2026-07-21):** AgentCore ships **explore**, **hybrid retrieval**, **change-risk**, and **architecture** overview over a Neo4j-backed code graph (MCP + CLI), with explicit ingest and session pending-sync freshness — not Repository Code Wiki and not continuous save-watch indexing.

This wedge answers one job:

1. Attach AgentCore to one or more repositories.
2. Keep an explicitly ingested structural and semantic model of the code and linked docs (session pending-sync banners; not always-live indexing).
3. Serve task-scoped context packs to IDE agents, autonomous workers, and human reviewers.
4. Measure whether outputs improved: acceptance rate, rework, defects, architecture drift, and token usage.

**Languages (v1 claims):** Python is required; TypeScript, JavaScript, Go, and Rust via the documented tree-sitter set only (`../07-code-knowledge-graph/10-language-support-policy.md`). Do not market other languages as supported.

### Platform expansion (architecture destination)

The same knowledge layer expands into a vendor-neutral control plane for agentic work: durable tickets, capability routing, governance, shared memory, audit, multi-agent coordination, and enterprise operations.

The control plane is the destination architecture. It is not the first sentence of the product promise. Features that coordinate many agents, departments, or approval systems must reuse the code-connected knowledge wedge rather than replace it.

### Normative boundary

AgentCore remains a control and knowledge plane, not an executor. See `07-agent-control-plane-product-boundary.md`. External agents perform task execution through versioned adapters. AgentCore owns registry, routing constraints, tickets, policy, shared context references, observability, and audit.

### v1 trust and isolation mode (backlog 34 Phase D)

| Mode | Allowed for v1 demos / sales? |
| --- | --- |
| **Single-tenant lab** (one tenant owns the deploy; optional IdP later) | **Yes** |
| **Multi-tenant SaaS** | **No** until GAP-005 enforcement suite stays green on production stores and remaining platform surfaces are covered |

Auth story for the wedge: document scope env (`AGENTCORE_TENANT_ID` / workspace / project) on MCP; do not claim multi-tenant IdP isolation as shipped. See `../09-platform-governance-operations/tenant-isolation-threat-model.md`.

### License / marketing hygiene (release checklist)

Before any external release or marketing claim:

- [ ] `docs/07-code-knowledge-graph/THIRD_PARTY_NOTICES.md` present and current
- [ ] Use “inspired by” wording for prior art; **no** false affiliation with CodeGraph / code-review-graph / graphify / CodeWiki
- [ ] Follow `docs/07-code-knowledge-graph/21-code-intelligence-prior-art-ideas-and-license.md`

## Core Product Promise

AgentCore improves AI-assisted software work through a closed loop:

```text
Repository  →  Structured code knowledge  →  Context injection  →  Better agent/IDE output  →  Measured gain
```

Concrete promises for the wedge:

1. Connected truth: the system knows what exists in the repository now, not only what was said in chat.
2. Relevant context: agents receive signatures, neighbors, docs, decisions, and constraints for the current task instead of raw repository dumps.
3. Better outputs: generated code and answers align with existing APIs, architecture, and project rules more often — including **removing orphaned predecessors** (dead symbols, unused imports, and exclusive tests) when an agent replaces or retires behavior, not only adding new code.
4. Lower waste: token use, retry loops, and abandoned diffs decrease when context is precise; leftover dead code does not accumulate as silent debt after AI edits.
5. Evidence of gain: teams can see whether speed, quality, architecture adherence, rework, token cost, and **measured dead-code cleanup** improved after connection.

The broader platform still answers the questions ordinary AI chat tools lose:

1. What happened?
2. Why did it happen?
3. What is the current truth?
4. Who or what must act next?
5. Which rules, documents, teams, and systems are affected?
6. Which repeated questions show missing knowledge?
7. Which work should be batched before memory, review, or documentation runs?
8. Which project scope owns this data?
9. Did the tool improve speed, quality, architecture, rework, and token usage?

Those nine questions remain valid. The wedge prioritizes questions 3, 5, and 9 first, because they are required to prove output improvement on a connected codebase.

## How the Wedge Works

### Connect

- Register a project and repository through connectors and project profiles.
- Isolate memory, graph, docs, tickets, and audit by project by default.
- Validate that the repository can be indexed and that adapters can receive context packs.

### Understand

- Parse code into a Code-Knowledge Graph: files, symbols, imports, calls, hashes, and relationships.
- Link documentation, decisions, issues, tasks, and rules to code anchors.
- Maintain current semantic state separately from raw activity history.
- Detect documentation drift and missing knowledge as structured gaps.

### Improve

- Build task-scoped context packs for IDE assistants and agent adapters.
- Prefer graph lookup, deterministic checks, and cached stable rules before expensive model calls.
- Run the **dead-code cleanup full loop** on coding tasks: surface unused-symbol / unused-file candidates from the Code-Knowledge Graph, seed always-on rules and skills that tell connected agents to delete proven-dead predecessors in the same change, and record cleanup outcomes — AgentCore never mutates the repository itself (external runtimes delete).
- Capture Activities, WorkLogs, corrections, and acceptance outcomes as evidence.
- Report benefit metrics against a baseline from before AgentCore context was enabled, including dead-code cleanup KPIs.

## Differentiation

AgentCore is not interchangeable with a generic repo RAG plugin or a standalone code graph viewer.

| Capability | Generic repo RAG / chat | Standalone code graph | AgentCore wedge |
|---|---|---|---|
| Retrieve snippets by similarity | Yes | Limited | Yes |
| Structural symbol and call graph | Rare | Yes | Yes |
| Living docs linked to symbols | Rare | Partial | Yes |
| Decisions, rules, and current truth injected with code | No | No | Yes |
| Adapter delivery into many agent/IDE runtimes | No | No | Yes |
| Measured output improvement loop | No | No | Yes |
| Dead-code candidates + cleanup guidance + measured cleanup | Rare | Partial (view-only) | Yes |
| Path to governed multi-agent control plane | No | No | Yes |

The differentiator is not “has a graph.” The differentiator is **code-connected knowledge that changes agent outputs and can prove it** — including cleaner diffs that remove orphaned code, not only add it — with a clean path to enterprise agent coordination.

## Primary Users

Wedge-first users:

- Developers using IDE-based assistants who need fewer wrong edits and less context thrash.
- Tech leads who want AI changes to respect existing architecture and APIs.
- Platform engineers connecting repositories, MCP/IDE adapters, and project profiles.

Platform expansion users:

- Engineering leaders who need visibility into AI-driven work.
- Autonomous backend, frontend, QA, data, DevOps, documentation, and security agents.
- Product managers and business owners who must approve high-risk changes.
- Product designers defining operator workflows, review surfaces, onboarding, and explainability UX.
- Compliance, support, and operations teams that depend on engineering events.
- Platform operators who install, connect, monitor, repair, and upgrade the system.

## Feature Catalog

Features are grouped by delivery priority. The catalog remains the full product surface; the wedge defines what must work first.

### A. Code connection and output improvement (wedge)

1. Repository and project connection: register repositories, project isolation, and connector validation.
2. Code-Knowledge Graph: files, classes, functions, methods, imports, calls, hashes, and relationships.
3. AST anchoring and change detection: stable symbol hashes for semantic diffs and doc drift.
4. Living documentation linked to code symbols (symbol-level). **Repository Code Wiki** (`14`–`18`) is **deferred** — not a v1 wedge claim (backlog `34` / Phase F).
5. Dynamic context injection: **explore** packs, **hybrid** BM25+semantic RRF search, generation context.
6. **Change-risk** (`detect_changes`) and **architecture** overview (communities, hubs, bridges, gaps).
7. State-over-event context: inject current truth before historical narratives.
8. Prompt caching for stable architecture and rules.
9. Vendor-agnostic adapters for IDE assistants and coding agents (MCP `programming-cursor-mcp`).
10. Human feedback and correction loop for wrong retrievals, drafts, and answers.
11. Impact reporting and benefit measurement for speed, quality, architecture, rework, tokens, and dead-code cleanup.
12. Dead-code cleanup full loop: unused-symbol / unused-file candidates from the graph, Workspace Guidance seed rule/skill so coding agents remove proven-dead predecessors in the same change, and cleanup benefit metrics (`../07-code-knowledge-graph/36-dead-code-candidates-and-cleanup-loop.md`).

### B. Structured memory and knowledge (supports the wedge)

13. Activity and Work Log: capture atomic agent actions, changed files, commands, tests, artifacts, and session summaries.
14. Decision Tracking: record architectural and product choices so future agents do not undo them blindly.
15. Issue and Task Separation: model discovered risk as an Issue and required work as Tasks.
16. Three-tier memory: working, episodic, and semantic.
17. Memory consolidation: compress raw activity into durable knowledge.
18. Decay and garbage collection: deprecate stale memory and rules when linked code or domains disappear.
19. Autonomous question discovery, FAQ memory, curiosity scoring, and missing documentation discovery.
20. Batched memory and deferred knowledge workflows.
21. Documentation knowledge graph with YAML frontmatter, Bloom filter lookup, and lightweight doc flags.

### C. Governance and multi-agent control plane (platform expansion)

22. Semantic rules and LLM-as-a-judge for ambiguous policy risks.
23. Escalation and human-in-the-loop approval.
24. Hybrid anomaly detection.
25. Dependency and impact analysis with downstream task generation.
26. Universal Agent JSON and central message broker / pub-sub.
27. Agent registry, capability routing, durable tickets, and lifecycle control.
28. Zero-touch installation and bootstrap.
29. Agent and resource connectivity automation.
30. Multi-project isolation and authorized project composition.
31. Admin web interface and agent control surface.
32. Cross-domain operating system beyond coding, after the coding wedge is proven.

## Non-Goals for Initial Delivery

- Replacing existing IDEs, ticket systems, CI systems, or agent vendors.
- Becoming “just another chat UI” over the repository.
- Training a custom foundation model.
- Claiming output improvement without measurable baselines and evidence.
- Auto-deleting repository files from AgentCore (external coding agents delete; AgentCore only candidates, guides, and measures).
- Repo-wide silent mass deletion; cleanup scope is the task neighborhood / symbols touched by the change.
- Allowing fully autonomous high-risk production changes without approval.
- Treating raw chat history as the permanent source of truth.
- Sharing project data across projects without explicit authorization and project composition policy.
- Creating noisy long-term memory from every small action or line-level edit.
- Leading the product narrative with multi-department orchestration before code-connected output improvement is credible.

## Acceptance Criteria for the Positioning

This product scope is satisfied when:

1. A new reader can state the wedge in one sentence: connect to code, improve AI outputs — via explore / hybrid / change-risk / architecture, including measured dead-code cleanup.
2. Design and implementation plans treat repository connection, code knowledge, context injection, benefit measurement, and the dead-code cleanup full loop as first-class wedge deliverables.
3. Control-plane features are documented as expansion on top of the wedge, not as a conflicting identity.
4. AgentCore is never specified as an agent runtime or LLM replacement; dead-code removal is executed by external agents only.
5. Differentiation from generic repo RAG and standalone code graphs is explicit in product and engineering docs.
6. Language claims match the Python + tree-sitter matrix; Code Wiki is not marketed as v1.
7. Embeddings default to real BGE (or clear LiteLLM path) with `embedding_backend` visible; stub is fallback only.
8. A new reader can state that better AI coding output means add/replace correctly **and** remove orphaned predecessors, with graph candidates, guidance, and measurable gain.

## Related Documents

- `05-complete-system-blueprint.md` — full narrative aligned to this positioning.
- `07-agent-control-plane-product-boundary.md` — normative executor vs control-plane boundary.
- `../07-code-knowledge-graph/01-vision-and-scope.md` — code graph as the core wedge mechanism.
- `../07-code-knowledge-graph/36-dead-code-candidates-and-cleanup-loop.md` — unused candidates, MCP contract, cleanup loop.
- `../07-code-knowledge-graph/14-repository-code-wiki-feature-specification.md` — Repository Code Wiki (CodeWiki-inspired).
- `../15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md` — seed rule/skill for cleanup during coding.
- `../09-platform-governance-operations/` — benefit measurement and operational controls.
