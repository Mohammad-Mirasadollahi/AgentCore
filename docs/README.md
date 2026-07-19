# AgentCore Documentation Plan

This documentation tree replaces the legacy flat documents numbered 0 through 5 with an indexed, phase-based English documentation set.

AgentCore is a vendor-neutral agent control plane for AI agents, human reviewers, tools, codebases, documentation, memory, policies, and cross-department workflows. AgentCore is not an agent and does not replace agent runtimes or frameworks. It registers and supervises external agents through adapters, routes durable tickets by capability, governs execution, and records structured evidence. Its core idea is simple: AI work should not disappear into chat history.

This documentation is written for experienced software engineers, software architects, product designers, platform operators, security reviewers, and technical decision makers. It is not written as beginner-level or general-audience product copy. Feature and architecture documents should be implementation-grade specifications that combine engineering behavior with product workflow, interaction states, permissions, diagnostics, metrics, and acceptance criteria.

## Implementation status

Executable vertical slices and phase gates for Phases 1–11 live under `backend/services/`, `backend/packages/`, `backend/configs/`, and `tests/backend/`. The repository root [README.md](../README.md) lists the phase map and named pytest commands. Product design docs in this tree remain the normative specification; gates prove slice completeness, not full production depth (for example Neo4j runtime remains a design target for the code graph).

**Usage Profiles** (org/person configuration + Cursor MCP): see [08-software-engineering-architecture/35-usage-profile-and-cursor-mcp-onboarding.md](08-software-engineering-architecture/35-usage-profile-and-cursor-mcp-onboarding.md).

## Documentation Map

- 00-master-plan/07-agent-control-plane-product-boundary.md is the normative product-boundary decision and must be read before agent, connector, orchestration, ticket, or model-runtime work.

- 00-master-plan/ defines the product scope, full feature catalog, roadmap, global architecture, cross-cutting challenges, complete system blueprint, professional documentation standard, documentation structure / machine-ingest standard (numbering, titles, frontmatter, RAG/GraphRAG, fallbacks), and documentation classification lanes (lifecycle, concern, audience, authority, visibility).
- 01-core-data-model/ defines Activity, WorkLog, Decision, Issue, and Task foundations.
- 02-memory-and-context/ defines three-tier memory, consolidation, state-over-event context, prompt caching, decay, dynamic retrieval, configurable memory weighting, autonomous question discovery, FAQ memory, curiosity scoring, missing documentation discovery, batched consolidation, and deferred documentation or review workflows.
- 03-docs-as-code-sync/ defines the documentation knowledge graph, AST anchoring, YAML frontmatter, Bloom filter lookup, and lightweight doc flags.
- 04-rule-engine-orchestration/ defines semantic rules, escalation, anomaly detection, dependency analysis, and task routing.
- 05-interoperability-ecosystem/ defines Universal Agent JSON, Pub/Sub broker, vendor adapters, IDE integrations, SDK and Developer Platform, Agent SDK, Adapter SDK, Admin SDK, Test SDK, and cross-domain workflows.
- 06-technical-logic/ is **Phase 6 (Technical Logic and Verification)**: domain algorithms and invariants for Phases 1 through 5, end-to-end runtime logic, technical test strategy, and the gated Definition of Done before Phase 7.
- 07-code-knowledge-graph/ defines the Neo4j-backed code graph, Tree-sitter ingestion, living documentation, graph-guided code generation, and token optimization design.
- 08-software-engineering-architecture/ defines the full software engineering playbook: principles, service boundaries, modular project structure, engineering operating model, domain modularization, contracts, persistence, quality attributes, tests, CI/CD, zero-touch installation, bootstrap automation, agent and resource connectivity automation, self-service operations, project isolation, project composition, domain packs, feature profiles, custom rule enablement, admin web interface, live testing, unit testing, local development, observability, extensibility, security, governance, onboarding, runtime topology, configuration rules, and development port conflict prevention.
- 09-platform-governance-operations/ defines security, observability, release strategy, retention, API governance, runbooks, automated deployment and connectivity procedures, impact reporting, benefit measurement, risk register, and glossary.
- 10-gap-analysis/ captures known gaps, unresolved assumptions, open decisions, and the process for reviewing and closing them.
- 11-logical-implementation-examples/ provides implementation-oriented logical examples and checklists for engineers who will code the system.

## Reading Order

1. Start with 00-master-plan/00-index.md.
2. Read 00-master-plan/05-complete-system-blueprint.md for the full product narrative.
3. Read 00-master-plan/06-professional-documentation-standard.md, 00-master-plan/08-documentation-structure-and-machine-ingest-standard.md, and 00-master-plan/09-documentation-classification-and-lanes.md before writing or reviewing new documents.
4. Read each phase folder in numeric order.
5. Inside each phase, read the local index file first, then follow the phase-specific file order listed there.
6. Read 02-memory-and-context/07-autonomous-question-discovery-and-faq-memory.md for repeated questions, curiosity scoring, FAQ memory, and missing documentation discovery.
7. Read 02-memory-and-context/08-batched-memory-and-deferred-knowledge-workflows.md for WorkBatch, deferred consolidation, deferred docs, and deferred code review.
8. Read 06-technical-logic/00-index.md for **Phase 6** (Technical Logic and Verification) before Phase 7 implementation.
9. Read 06-technical-logic/06-end-to-end-runtime-logic.md before the phase-level technical logic files, then 08 through 12 for the Phase 6 design package and gate.
10. Read 07-code-knowledge-graph/00-index.md for graph-backed code understanding, living documentation, and graph-guided code generation only after the Phase 6 gate is understood.
11. Read 08-software-engineering-architecture/00-index.md for the complete engineering playbook.
12. Read 08-software-engineering-architecture/05-modular-project-structure.md before creating repository folders or new modules.
13. Read 08-software-engineering-architecture/06-engineering-operating-model.md before planning implementation work.
14. Read 08-software-engineering-architecture/08-interface-and-contract-engineering.md before changing APIs, events, SDKs, config schemas, adapter payloads, or graph contracts.
15. Read 05-interoperability-ecosystem/07-sdk-and-developer-platform.md and 08-software-engineering-architecture/27-sdk-engineering-and-contract-generation.md before implementing SDK packages, generated clients, adapter SDKs, agent SDKs, admin SDKs, test SDKs, or SDK release pipelines.
16. Read 08-software-engineering-architecture/11-testing-and-verification-engineering.md before writing verification plans.
17. Read 08-software-engineering-architecture/19-zero-touch-installation-and-bootstrap-automation.md before designing installation, bootstrap, generated configuration, first-run readiness, or installation evidence reports.
18. Read 08-software-engineering-architecture/20-agent-and-resource-connectivity-automation.md before designing agent onboarding, connector registration, capability discovery, connection profiles, or resource integration.
19. Read 08-software-engineering-architecture/21-automation-control-plane-and-self-service-operations.md before designing self-service operations, automated repair, drift detection, upgrades, or diagnostics bundles.
20. Read 08-software-engineering-architecture/22-product-design-and-engineering-specification-discipline.md before writing feature specifications, product experience specifications, operator workflows, or implementation-ready technical designs.
21. Read 08-software-engineering-architecture/23-project-isolation-and-composition-architecture.md before designing multi-project, project-group, memory scope, graph scope, report scope, or connector scope behavior.
22. Read 08-software-engineering-architecture/24-admin-web-interface-and-agent-control-surface.md before designing the web interface, agent control surface, memory management, task management, rule management, feedback, or tracking workflows.
23. Read 08-software-engineering-architecture/25-live-and-unit-test-strategy.md before designing Unit Tests, Live Tests, release validation, real-data safety, or test evidence workflows.
24. Read 08-software-engineering-architecture/26-domain-customization-and-feature-control.md before designing domain packs, feature profiles, user-defined rules, feature hiding, or conversation-based rule suggestions.
25. Read 08-software-engineering-architecture/13-local-development-and-environment-engineering.md before running local or remote development stacks.
26. Read 08-software-engineering-architecture/18-developer-onboarding-and-delivery-workflow.md when onboarding or preparing a delivery checklist.
27. Read 09-platform-governance-operations/10-impact-reporting-and-benefit-measurement.md before designing reports for speed, bug reduction, architecture quality, rework, or token consumption.
28. Read 09-platform-governance-operations/00-index.md for operational governance, security, observability, release, retention, automated deployment, connectivity runbooks, impact reporting, and operational procedures.
29. Read 10-gap-analysis/00-index.md to review unresolved gaps, assumptions, and decisions that need future thinking.
30. Read 11-logical-implementation-examples/00-index.md to see concrete examples of how the system should behave when implemented.

## compatible IDE agent documentation (not product scope)

Configuring **IDE** rules, skills, and optional team workspace packs is documented separately from AgentCore product phases:

- Start at [`docs/agents/00-index.md`](agents/00-index.md) (canonical source: `ai-toolstack/docs/agents/00-index.md`, synced on `install.sh`).
- Workspace rule interview: [`docs/agents/ide-workspace-rule-discovery.md`](agents/ide-workspace-rule-discovery.md).

This does not implement the platform rule engine under `04-rule-engine-orchestration/`.

## Replacement Goal

The old flat documents numbered 0 through 5 have been replaced. Combined design documents have also been split into separate phase-specific design files. The documentation now includes feature scope, separate design files, contracts, challenges, acceptance criteria, detailed rationale, scenarios, edge cases, operational design guidance, technical logic, algorithms, graph-backed code understanding, modular project structure, a broad software engineering playbook, professional product design and engineering specification discipline, zero-touch installation, automated bootstrap, agent and resource connectivity automation, self-service operations, autonomous question discovery, FAQ memory, batched knowledge workflows, project isolation, project composition, domain packs, feature profiles, custom rule authoring, conversation-based rule suggestions, SDK platform, SDK generation, SDK testing, admin web interface, impact reporting, Unit Test strategy, Live Test strategy, port conflict prevention, operational governance, runbooks, risk tracking, gap analysis, logical implementation examples, and verification strategy.
31. Read `/root/AgentCore/backend/docs/STRUCTURE_STANDARD.md` before creating or moving backend folders.
- `13-technology-stack-and-platform-decisions/` defines the selected technology stack: Next.js, TypeScript, Python, FastAPI, PostgreSQL, pgvector, Neo4j, Redis, object storage, messaging, observability, and deployment profiles.
- `14-api-design-and-naming-standards/` defines API endpoint naming, DTO naming, error format, pagination, idempotency, API catalog, OpenAPI, SDK, and contract governance.
