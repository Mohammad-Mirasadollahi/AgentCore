# Product Scope and Feature Catalog

## Vision

AgentCore connects to a codebase and improves the outputs of connected AI coding tools.

It indexes repository structure, documentation, decisions, and current project truth, then injects only the relevant context into IDE assistants, agent runtimes, and review workflows. The measurable result is better code and answers: fewer hallucinations, less rework, lower token cost, and clearer impact awareness.

AgentCore is not an agent, an LLM, a coding IDE, or a replacement for agent frameworks. Connected runtimes still write the code. AgentCore owns the code-linked knowledge layer that makes those runtimes produce better work.

## Product Positioning

### Wedge product (delivery focus)

The first product users must understand and adopt is:

**Connect a repository → build structured code knowledge → improve AI outputs on that repository.**

This wedge answers one job:

1. Attach AgentCore to one or more repositories.
2. Keep a live structural and semantic model of the code and linked docs.
3. Serve task-scoped context packs to IDE agents, autonomous workers, and human reviewers.
4. Measure whether outputs improved: acceptance rate, rework, defects, architecture drift, and token usage.

### Platform expansion (architecture destination)

The same knowledge layer expands into a vendor-neutral control plane for agentic work: durable tickets, capability routing, governance, shared memory, audit, multi-agent coordination, and enterprise operations.

The control plane is the destination architecture. It is not the first sentence of the product promise. Features that coordinate many agents, departments, or approval systems must reuse the code-connected knowledge wedge rather than replace it.

### Normative boundary

AgentCore remains a control and knowledge plane, not an executor. See `07-agent-control-plane-product-boundary.md`. External agents perform task execution through versioned adapters. AgentCore owns registry, routing constraints, tickets, policy, shared context references, observability, and audit.

## Core Product Promise

AgentCore improves AI-assisted software work through a closed loop:

```text
Repository  →  Structured code knowledge  →  Context injection  →  Better agent/IDE output  →  Measured gain
```

Concrete promises for the wedge:

1. Connected truth: the system knows what exists in the repository now, not only what was said in chat.
2. Relevant context: agents receive signatures, neighbors, docs, decisions, and constraints for the current task instead of raw repository dumps.
3. Better outputs: generated code and answers align with existing APIs, architecture, and project rules more often.
4. Lower waste: token use, retry loops, and abandoned diffs decrease when context is precise.
5. Evidence of gain: teams can see whether speed, quality, architecture adherence, rework, and token cost improved after connection.

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
- Capture Activities, WorkLogs, corrections, and acceptance outcomes as evidence.
- Report benefit metrics against a baseline from before AgentCore context was enabled.

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
| Path to governed multi-agent control plane | No | No | Yes |

The differentiator is not “has a graph.” The differentiator is **code-connected knowledge that changes agent outputs and can prove it**, with a clean path to enterprise agent coordination.

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
4. Living documentation linked to code symbols, and Repository Code Wiki for holistic, architecture-aware repository-level documentation (hierarchical modules, incremental refresh, Mermaid visuals, admin browse + MCP); see `../07-code-knowledge-graph/14-repository-code-wiki-feature-specification.md`.
5. Dynamic context injection and RAG: retrieve only task-relevant code, docs, and state.
6. State-over-event context: inject current truth before historical narratives.
7. Prompt caching for stable architecture and rules.
8. Vendor-agnostic adapters for IDE assistants and coding agents.
9. Human feedback and correction loop for wrong retrievals, drafts, and answers.
10. Impact reporting and benefit measurement for speed, quality, architecture, rework, and tokens.

### B. Structured memory and knowledge (supports the wedge)

11. Activity and Work Log: capture atomic agent actions, changed files, commands, tests, artifacts, and session summaries.
12. Decision Tracking: record architectural and product choices so future agents do not undo them blindly.
13. Issue and Task Separation: model discovered risk as an Issue and required work as Tasks.
14. Three-tier memory: working, episodic, and semantic.
15. Memory consolidation: compress raw activity into durable knowledge.
16. Decay and garbage collection: deprecate stale memory and rules when linked code or domains disappear.
17. Autonomous question discovery, FAQ memory, curiosity scoring, and missing documentation discovery.
18. Batched memory and deferred knowledge workflows.
19. Documentation knowledge graph with YAML frontmatter, Bloom filter lookup, and lightweight doc flags.

### C. Governance and multi-agent control plane (platform expansion)

20. Semantic rules and LLM-as-a-judge for ambiguous policy risks.
21. Escalation and human-in-the-loop approval.
22. Hybrid anomaly detection.
23. Dependency and impact analysis with downstream task generation.
24. Universal Agent JSON and central message broker / pub-sub.
25. Agent registry, capability routing, durable tickets, and lifecycle control.
26. Zero-touch installation and bootstrap.
27. Agent and resource connectivity automation.
28. Multi-project isolation and authorized project composition.
29. Admin web interface and agent control surface.
30. Cross-domain operating system beyond coding, after the coding wedge is proven.

## Non-Goals for Initial Delivery

- Replacing existing IDEs, ticket systems, CI systems, or agent vendors.
- Becoming “just another chat UI” over the repository.
- Training a custom foundation model.
- Claiming output improvement without measurable baselines and evidence.
- Allowing fully autonomous high-risk production changes without approval.
- Treating raw chat history as the permanent source of truth.
- Sharing project data across projects without explicit authorization and project composition policy.
- Creating noisy long-term memory from every small action or line-level edit.
- Leading the product narrative with multi-department orchestration before code-connected output improvement is credible.

## Acceptance Criteria for the Positioning

This product scope is satisfied when:

1. A new reader can state the wedge in one sentence: connect to code, improve AI outputs.
2. Design and implementation plans treat repository connection, code knowledge, context injection, and benefit measurement as first-class wedge deliverables.
3. Control-plane features are documented as expansion on top of the wedge, not as a conflicting identity.
4. AgentCore is never specified as an agent runtime or LLM replacement.
5. Differentiation from generic repo RAG and standalone code graphs is explicit in product and engineering docs.

## Related Documents

- `05-complete-system-blueprint.md` — full narrative aligned to this positioning.
- `07-agent-control-plane-product-boundary.md` — normative executor vs control-plane boundary.
- `../07-code-knowledge-graph/01-vision-and-scope.md` — code graph as the core wedge mechanism.
- `../07-code-knowledge-graph/14-repository-code-wiki-feature-specification.md` — Repository Code Wiki (CodeWiki-inspired).
- `../09-platform-governance-operations/` — benefit measurement and operational controls.
