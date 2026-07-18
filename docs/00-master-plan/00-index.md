# 00 - Master Plan Index

## Purpose

This folder describes the complete AgentCore plan at product and architecture level. It is the entry point for professional readers who need the whole system before going into phase-specific design. The documentation is written for experienced software engineers, architects, product designers, operators, security reviewers, and technical decision makers rather than a general audience.

## Files

- 01-product-scope-and-feature-catalog.md explains the target product, users, full feature set, and non-goals.
- 02-roadmap-and-phase-gates.md defines implementation phases, sequencing, dependencies, and exit criteria.
- 03-global-architecture-hld.md provides the system-wide high-level architecture.
- 04-cross-cutting-challenges.md captures challenges that affect multiple phases.
- 05-complete-system-blueprint.md provides the full product and architecture narrative.
- 06-professional-documentation-standard.md defines the professional documentation standard for writing implementation-grade engineering and product design specifications.
- 08-documentation-structure-and-machine-ingest-standard.md defines tree numbering, titles, frontmatter, RAG/LLMIndex/GraphRAG authoring shape, and fallback ingest tiers.

## Phase Folders

- Phase 1: Core Data Model
- Phase 2: Memory and Token Optimization
- Phase 3: Docs-as-Code and Synchronization
- Phase 4: Rule Engine and Orchestration
- Phase 5: Interoperability and Enterprise Ecosystem
- Phase 6: Technical Logic and Verification (`../06-technical-logic/`, gated in `02-roadmap-and-phase-gates.md`)
- Phase 7: Code-Knowledge Graph
- Phase 8: Software Engineering Architecture
- Phase 9: Platform Governance and Operations
- Phase 10: Gap Analysis
- Phase 11: Logical Implementation Examples

## Phase 6 / Technical Section

Phase 6 is a first-class roadmap phase. Its design home is `../06-technical-logic/`. That folder contains phase-design files plus algorithms, state machines, invariants, runtime flow, failure handling, and the technical test strategy that verifies Phases 1 through 5 before Phase 7 begins.

## Code-Knowledge Graph Section

The Neo4j-backed code understanding and graph-guided code generation design is documented in ../07-code-knowledge-graph/.

## Software Engineering Architecture Section

The full software engineering playbook is documented in ../08-software-engineering-architecture/. It covers architecture principles, service boundaries, modular project structure, engineering operating model, domain-driven modularization, interface and contract engineering, data and persistence engineering, quality attributes, testing, CI/CD, release engineering, zero-touch installation, automated bootstrap, agent and resource connectivity automation, self-service operations, local and remote development, observability, extensibility, security engineering, threat modeling, governance, change control, onboarding, runtime topology, configuration model, and development port conflict prevention.

Engineers and product designers should read 06-professional-documentation-standard.md and 08-documentation-structure-and-machine-ingest-standard.md before writing or reviewing new documents. Engineers should then read ../08-software-engineering-architecture/00-index.md first, and ../08-software-engineering-architecture/05-modular-project-structure.md before creating repository folders, services, packages, tools, scripts, configuration profiles, or cross-module tests.

## Platform Governance and Operations Section

Security, observability, release strategy, data retention, API governance, runbooks, automated deployment and connectivity procedures, risk register, and glossary are documented in ../09-platform-governance-operations/.

## Gap Analysis Section

Known gaps, unresolved assumptions, open decisions, and the gap triage process are documented in ../10-gap-analysis/.

## Logical Implementation Examples Section

Concrete implementation-oriented examples, runtime scenarios, and developer checklists are documented in ../11-logical-implementation-examples/.
- `07-agent-control-plane-product-boundary.md` is the normative decision that AgentCore manages external agents and is not itself an agent or agent framework.
