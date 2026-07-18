# Master Gap Register

## Purpose

This register lists the most important gaps currently visible in the AgentCore design. Each gap should eventually become a Decision, Task, Risk, or accepted non-goal.

## GAP-001 - Storage Boundary Finalization

Category: Architecture

Severity: High

Impact: The documentation defines multiple storage types, but final ownership between relational storage, Neo4j, object storage, broker persistence, vector indexes, and configuration storage still needs a concrete implementation decision.

Why it matters: Incorrect storage ownership can create duplicate truth, difficult migrations, and inconsistent audit behavior.

Current assumption: Core entities live outside Neo4j, code relationships live in Neo4j, artifacts live in object storage, and events live in broker persistence or event storage.

Decision needed: Define the authoritative storage location for every entity type and event type.

Suggested owner: Platform Architect

Resolution path: Create a storage ownership matrix and update data contracts.

Status: DECISION_NEEDED

## GAP-002 - First Supported Language Set

Category: Technical Implementation

Severity: High

Impact: Tree-sitter supports many languages, but the first implementation must choose supported languages and parser behavior.

Why it matters: Symbol extraction, call resolution, import resolution, and AST hashing differ by language.

Current assumption: The system starts with a small language set before expanding.

Decision needed: Choose initial language support and define parser confidence rules per language.

Suggested owner: Code Graph Lead

Resolution path: Create language support matrix and parser acceptance tests.

Status: OPEN

## GAP-003 - LLM Provider and Local Model Strategy

Category: Technical Implementation

Severity: High

Impact: The design references local and cloud models, but default routing and fallback behavior need concrete selection.

Why it matters: Cost, latency, privacy, and quality depend on model routing.

Current assumption: Low-risk documentation can use local or low-cost models; complex code generation and high-risk judgment use stronger models.

Decision needed: Define model routing profiles by task type, risk level, tenant, and environment.

Suggested owner: AI Platform Lead

Resolution path: Benchmark models and create default ModelRoutingProfile.

Status: DECISION_NEEDED

## GAP-004 - Human Approval UX

Category: Product and Workflow

Severity: Medium

Impact: The system defines escalation tickets but does not yet define the exact UI or integration surface for approvals.

Why it matters: Poor approval UX will slow teams and cause rubber-stamping.

Current assumption: Approval can happen through platform UI, IDE, Slack, Jira, or other workflow tools.

Decision needed: Choose first approval surface and required approval interaction model.

Suggested owner: Product Lead

Resolution path: Design approval workflow and add UI/API contract.

Status: OPEN

## GAP-005 - Tenant Isolation Implementation Details

Category: Security

Severity: Critical

Impact: Tenant isolation is required, but exact implementation across graph, memory, broker, object storage, and vector indexes needs more detail.

Why it matters: Tenant boundary failure is a critical security issue.

Current assumption: Every entity and event carries tenant ID and access checks run before retrieval or delivery.

Decision needed: Define isolation enforcement strategy per storage and service boundary.

Suggested owner: Security Architect

Resolution path: Create tenant isolation threat model and test plan.

Status: UNDER_REVIEW

## GAP-006 - Weight Profile Governance

Category: Memory and Retrieval

Severity: Medium

Impact: WeightProfiles and GraphRetrievalProfiles are defined, but ownership, approval, and rollback policy are not yet fully specified.

Why it matters: Bad weights can hide important memory or over-prioritize stale context.

Current assumption: Profiles are versioned and auditable.

Decision needed: Define who can change profiles and how changes are validated.

Suggested owner: Memory Platform Lead

Resolution path: Add governance workflow and profile change tests.

Status: OPEN

## GAP-007 - Development Port Profile Ownership

Category: Developer Experience

Severity: Medium

Impact: Non-default development ports are documented, but ownership of the default profile and update process needs definition.

Why it matters: Conflicting local setups can create friction if port policy is unclear.

Current assumption: Development ports are configurable and project-scoped.

Decision needed: Choose default development base and ownership of port profile changes.

Suggested owner: Developer Experience Lead

Resolution path: Port profile file format and Phase 8 gate ownership checks.

Status: CLOSED

Closed in: Phase 8 port-profile catalog and verification gate (`docs/08-software-engineering-architecture/34-phase8-verification-and-acceptance.md`).

## GAP-008 - Schema Registry Implementation

Category: Contract Governance

Severity: Medium

Impact: Schema registry is recommended but not implemented in the design as a concrete service or repository module.

Why it matters: Without schema registry, broker events and adapter contracts may drift.

Current assumption: A versioned schema catalog exists.

Decision needed: Decide whether schema registry is a service, repo directory, or database-backed registry.

Suggested owner: Platform Architect

Resolution path: Create schema registry architecture note.

Status: DECISION_NEEDED

## GAP-009 - Domain Pack, Feature Profile, And Rule Suggestion Governance

Category: Product Architecture and Configuration Governance

Severity: High

Impact: AgentCore now defines domain packs, feature profiles, user-authored rules, and conversation-derived rule suggestions, but the final schema ownership, approval workflow, conflict resolution policy, and rollout model still need implementation-level decisions.

Why it matters: These mechanisms control what users see, what agents can do, which rules apply, and how non-engineering domains are simplified. A weak governance model could cause confusing behavior, accidental feature exposure, cross-project leakage, or unsafe automatic rule activation.

Current assumption: Domain packs, feature profiles, and suggested rules are versioned, scoped, auditable, dry-run capable, and approval-gated by default.

Decision needed: Define the authoritative schema, ownership model, activation workflow, conflict precedence rules, UI review flow, test fixture format, and default first-party domain packs.

Suggested owner: Product Architect and Platform Architect

Resolution path: Create a formal DomainPack schema, FeatureProfile schema, RuleSuggestion schema, conflict-resolution matrix, admin-console workflow, and acceptance test suite.

Status: DECISION_NEEDED

## GAP-010 - Impact KPI Instrumentation Completeness

Category: Governance and Operations

Severity: Medium

Impact: Impact KPIs need machine-checkable fields and an explicit comparison method.

Why it matters: Without instrumentation completeness, benefit reporting cannot be audited.

Current assumption: KPI catalogs are versioned and gate-checked.

Decision needed: Ensure KPI fields and comparison method are machine-checkable.

Suggested owner: Platform Governance Lead

Resolution path: Impact KPI catalog and Phase 9 gate.

Status: CLOSED

Closed in: Phase 9 impact-kpis catalog and verification gate (`docs/09-platform-governance-operations/11-phase9-verification-and-acceptance.md`).

## GAP-011 - Neo4j as Code Graph Store Timing

Category: Architecture

Severity: Medium

Impact: Phase 7 uses a Postgres `code_graph` slice while Neo4j remains the design target for production graph storage.

Why it matters: Delayed migration can create dual-write debt; early migration can block language-matrix work.

Current assumption: Postgres slice is acceptable until the language support matrix lands.

Decision needed: When to migrate from Postgres code_graph schema to Neo4j in production.

Suggested owner: Code Graph Lead

Approver: Platform Architect

Review date: 2026-10-01

Resolution path: Keep Postgres slice for Phase 7; schedule Neo4j cutover after language matrix lands.

Status: ACCEPTED_RISK
