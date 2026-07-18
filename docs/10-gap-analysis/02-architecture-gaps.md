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
