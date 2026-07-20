# Architecture Gaps

## Purpose

This document captures architecture-level gaps that should be resolved before implementation reaches production-grade design.

## GAP-A01 - Bounded Context Map

The documentation defines many services, but it still needs a formal bounded context map.

Questions:

- Which service owns each entity?
- Which services are allowed to read each entity?
- Which services receive events rather than direct reads?
- Which service owns schema migration for each table or graph label?

Resolution output:

- Bounded context diagram.
- Entity ownership matrix.
- Allowed dependency direction map.

## GAP-A02 - Synchronous vs Asynchronous Boundaries

The design references synchronous APIs and asynchronous jobs, but exact boundaries need definition.

Questions:

- Which operations must complete inside a user request?
- Which operations can be delayed as jobs?
- Which events require durable delivery?
- Which workflows must be eventually consistent?

Resolution output:

- Runtime sequence diagrams.
- Async job catalog.
- Retry and timeout policy.

## GAP-A03 - Read Model Strategy

AgentCore may need multiple read models for dashboard, audit, retrieval, graph queries, and operational metrics.

Questions:

- Which read models are materialized?
- Which are built on demand?
- How are read models invalidated?
- How does the system avoid stale dashboard or prompt context?

Resolution output:

- Read model design.
- Consistency model per read path.

## GAP-A04 - Multi-Tenant Deployment Modes

The design requires tenant isolation, but deployment mode choices are still open.

Possible modes:

- shared services with tenant-scoped data,
- isolated database per tenant,
- isolated graph per tenant,
- isolated deployment per enterprise customer.

Resolution output:

- tenancy deployment decision.
- cost and security tradeoff analysis.

## GAP-A05 - Agent Trust Model

Agent capability profiles are documented, but a complete trust model is still needed.

Questions:

- How does an agent earn higher trust?
- How is trust revoked?
- How are model providers ranked by trust?
- How do failed tasks affect agent trust?

Resolution output:

- Agent trust lifecycle.
- Capability approval workflow.
- Trust scoring policy.

## GAP-A06 - Product Boundary Between AgentCore and IDEs

AgentCore integrates with IDEs, but exact product boundary must be defined.

Questions:

- Which actions happen inside the IDE plugin?
- Which actions happen in AgentCore web UI?
- Which actions happen through CLI or API?
- How does context injection appear to developers?

Resolution output:

- Interaction model.
- First IDE integration scope.
- Developer workflow diagrams.

**Documentation update (2026-07-20):** Connect-time guidance injection shape is specified in [`../15-agent-workspace-guidance/`](../15-agent-workspace-guidance/) (MCP-primary resolve of AGENTS entry / always-on rules / skills, optional filesystem export; Common Context as SoT). This closes the design gap for “how context injection appears” at the guidance-artifact layer. Remaining open: IDE plugin chrome, in-IDE banners, and hard “resolve before write” enforcement. See phase 15 risks doc for residual items. Status: **partially addressed (design docs)**; implementation still open.

## GAP-A07 - Enterprise Administration Model

The documentation references tenants, profiles, policies, adapters, and port profiles, but admin workflows need more detail.

Questions:

- Who can create tenants?
- Who can create projects?
- Who can approve policies?
- Who can change WeightProfiles?
- Who can install adapters?

Resolution output:

- Admin role model.
- Permission matrix.
- Audit requirements for admin changes.

## GAP-A08 - Agent Collaboration Surface Completeness

Issue, Task, and AgentTicket existed, but Pull Request–like ChangeSet, review threads, discussion comments, and labels were underspecified for agent-native collaboration (without GitHub as SoR).

Questions:

- What is the native PR analog and its state machine?
- How do reviews relate to AgentTicket `:submit-review` and EscalationTicket?
- How do external GitHub/Jira objects map without becoming SoR?

Partial resolution:

- Product surface: `../01-core-data-model/07-agent-collaboration-work-surface.md`
- Contracts: `../01-core-data-model/08-changeset-review-and-discussion-contracts.md`
- External mapping: `../05-interoperability-ecosystem/10-external-vcs-and-tracker-mapping.md`

Still open:

- Diff viewer UX and artifact streaming.
- Whether WorkMilestone ships with ChangeSet MVP.
- EscalationTicket vs ApprovalRequest vs ApprovalTicket naming unification.

Status: `PLANNED` (docs proposed; implementation not started).
