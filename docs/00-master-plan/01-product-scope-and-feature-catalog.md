# Product Scope and Feature Catalog

## Vision

AgentCore is a vendor-neutral control plane for autonomous and semi-autonomous agents inside an organization. It turns fragmented AI interactions into structured, governed, reusable operational knowledge while leaving task execution inside connected agent runtimes.

AgentCore is not an agent, an LLM, or a replacement for agent frameworks. Codex, IDE-based workers, LangChain applications, custom agents, and future runtimes are managed resources connected through adapters. AgentCore owns registry, capability routing, tickets, governance, shared context, observability, audit, and lifecycle control.

The platform is not only a coding assistant. It is a coordination system that gives agents and humans a common memory, common protocol, common policy layer, common documentation graph, common task model, common project isolation model, common reporting layer, and common control surface.

## Core Product Promise

AgentCore answers nine questions that ordinary AI chat tools usually lose:

1. What happened?
2. Why did it happen?
3. What is the current truth?
4. Who or what must act next?
5. Which rules, documents, teams, and systems are affected?
6. Which repeated questions show missing knowledge?
7. Which work should be batched before memory, review, or documentation runs?
8. Which project scope owns this data?
9. Did the tool improve speed, quality, architecture, rework, and token usage?

## Primary Users

- Engineering leaders who need visibility into AI-driven work.
- Developers using IDE-based assistants such as IDE or similar tools.
- Autonomous backend, frontend, QA, data, DevOps, documentation, and security agents.
- Product managers and business owners who must approve high-risk changes.
- Product designers designing operator workflows, review surfaces, onboarding, state models, and explainability UX.
- Compliance, support, marketing, HR, and operations teams that depend on engineering events.
- Platform operators who install, connect, monitor, repair, and upgrade the system.

## Feature Catalog

1. Activity and Work Log: capture atomic agent actions, changed files, commands, tests, artifacts, and session summaries.
2. Decision Tracking: record the reason behind architectural and product choices so future agents do not undo them blindly.
3. Issue and Task Separation: model a discovered risk as an Issue and the required work as one or more Tasks.
4. Three-Tier Memory: separate working, episodic, and semantic memory.
5. Memory Consolidation: compress raw activity into durable knowledge.
6. State over Event Context: inject current truth before historical narratives.
7. Decay and Garbage Collection: deprecate stale memory and rules when linked code or domains disappear.
8. Prompt Caching: keep stable rules and architecture in cache-friendly prompt sections.
9. Dynamic Context Injection and RAG: retrieve only task-relevant context.
10. Autonomous Question Discovery: detect repeated or unanswered questions and treat them as knowledge gap signals.
11. FAQ Memory: promote stable, frequently asked, evidence-backed answers into scoped project or workspace memory.
12. Curiosity Scoring: score whether the system should proactively investigate a question, missing answer, or missing documentation.
13. Missing Documentation Discovery: detect when code, functions, rules, APIs, or workflows lack documentation and create drafts, Tasks, or Gaps.
14. Batched Memory and Deferred Knowledge Workflows: group related activity into WorkBatch units before memory consolidation, documentation generation, or code review.
15. Documentation Knowledge Graph: link docs, code, decisions, issues, tasks, and owners.
16. AST Anchoring: detect semantic code changes through stable symbol hashes.
17. YAML Frontmatter: make Markdown readable by humans and routable by machines.
18. Bloom Filter Lookup: quickly skip symbols that definitely have no documentation.
19. Lightweight y/n Doc Flags: use simple manifest or inline flags to guide documentation lookup.
20. Semantic Rules and LLM-as-a-Judge: evaluate natural-language policies for ambiguous risks.
21. Escalation and Human-in-the-Loop: stop risky automation and request approval.
22. Hybrid Anomaly Detection: run cheap checks first and invoke LLM review only when useful.
23. Dependency and Impact Analysis: estimate blast radius and generate downstream tasks.
24. Universal Agent JSON: define a common structured language between agents.
25. Central Message Broker and Pub/Sub: publish events to subscribers without direct coupling.
26. Vendor-Agnostic Adapters: connect different AI tools, IDEs, and model providers.
27. Zero-Touch Installation and Bootstrap: install dependencies, generate configuration, provision stores, run migrations, start services, and validate readiness with minimal manual work.
28. Agent and Resource Connectivity Automation: register agents, repositories, IDEs, ticket systems, model providers, and other resources through generated profiles and validation.
29. Multi-Project Isolation: keep project memory, graph, docs, tickets, agents, reports, and audit data isolated by default.
30. Project Composition: explicitly combine related projects such as frontend and backend through authorized ProjectGroup policies.
31. Admin Web Interface and Agent Control Surface: track actions, manage memory, tasks, tickets, rules, agents, connectors, batches, automation jobs, reports, corrections, and audit.
32. Human Feedback and Correction Loop: let users correct wrong answers, memory retrieval, documentation drafts, rules, scope decisions, and task decomposition so future behavior improves.
33. Impact Reporting and Benefit Measurement: report code generation speed, bug reduction, architecture quality, rework reduction, and token consumption with baselines.
34. Cross-Domain Operating System: extend the same agent coordination model beyond coding.

## Non-Goals for Initial Delivery

- Replacing existing IDEs, ticket systems, CI systems, or agent vendors.
- Training a custom foundation model.
- Allowing fully autonomous high-risk production changes without approval.
- Treating raw chat history as the permanent source of truth.
- Sharing project data across projects without explicit authorization and project composition policy.
- Creating noisy long-term memory from every small action or line-level edit.
