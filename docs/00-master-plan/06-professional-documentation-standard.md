# 06 - Professional Documentation Standard

## Purpose

AgentCore documentation is not intended for a casual reader or a non-technical audience. The documentation must be written for experienced software engineers, software architects, product designers, platform operators, security reviewers, and technical decision makers who need enough detail to design, implement, validate, operate, and evolve the system.

For **tree layout, file numbering, titles, YAML frontmatter, RAG/LLMIndex chunking, GraphRAG link hints, and fallback ingest**, follow `08-documentation-structure-and-machine-ingest-standard.md`. This document owns audience, tone, and required content sections.

Every document should behave like an implementation-grade product and engineering specification. It should explain not only what the system should do, but also why the behavior exists, which actors use it, which modules own it, which contracts expose it, which data it changes, which edge cases exist, how it is verified, and how it appears in the product experience.

## Target Readers

The primary readers are:

- senior software engineers implementing services, packages, APIs, events, workers, stores, tests, and automation.
- software architects reviewing boundaries, runtime topology, quality attributes, and cross-service contracts.
- product designers defining workflows, information architecture, interaction states, onboarding paths, and operator experience.
- product managers evaluating scope, phase gates, acceptance criteria, and enterprise readiness.
- platform operators deploying, monitoring, diagnosing, repairing, and upgrading the system.
- security reviewers validating trust boundaries, authorization, prompt safety, tenant isolation, and approval workflows.
- future AI agents using the documentation as structured implementation context.

The documentation should assume the reader understands professional software delivery concepts such as bounded contexts, contracts, event-driven systems, migrations, observability, CI/CD, RBAC, state machines, and product workflow design.

## Documentation Tone

The tone should be technical, precise, and decision-oriented.

Allowed tone:

- explicit engineering requirements.
- product behavior expressed as workflows, states, and constraints.
- implementation consequences and tradeoffs.
- measurable acceptance criteria.
- concrete examples with realistic payload, state, or module behavior.
- professional product design language such as task model, information architecture, interaction states, user roles, service blueprint, error recovery, and progressive disclosure.

Avoid:

- generic marketing language.
- vague product promises.
- beginner-level explanations of common engineering concepts.
- unsupported claims such as easy, smart, seamless, or powerful without defined behavior.
- feature descriptions that do not map to modules, contracts, states, or tests.
- UI descriptions that ignore empty, loading, error, permission, degraded, and recovery states.

## Required Perspective

Every major document should combine two perspectives.

### Software Engineering Perspective

A software engineering perspective should define:

- module ownership.
- service boundaries.
- public contracts.
- commands and queries.
- events and event envelope requirements.
- data model and persistence ownership.
- state transitions and invariants.
- failure modes.
- idempotency and retry behavior.
- security and authorization constraints.
- observability and diagnostics.
- test strategy.
- deployment and configuration impact.
- acceptance criteria.

### Product Design Perspective

A product design perspective should define:

- target roles and permissions.
- primary jobs to be done.
- user and agent journeys.
- information architecture.
- navigation and task flow.
- interaction states.
- empty states.
- loading states.
- error states.
- partial success states.
- degraded states.
- approval and review states.
- onboarding and setup flow.
- copy requirements for high-risk or technical actions.
- accessibility and usability constraints.
- product telemetry and success metrics.

Product design is not only visual design. In AgentCore, product design includes the shape of technical workflows, operator ergonomics, review surfaces, decision traceability, and how agents and humans understand system state.

## Required Sections For Feature Documents

A feature document should include these sections when applicable:

- Purpose.
- Professional Audience.
- Problem Statement.
- Goals.
- Non-Goals.
- Actors And Permissions.
- Product Workflow.
- Interaction State Model.
- Information Architecture Impact.
- System Behavior.
- Owning Modules.
- Public Contracts.
- Data Model Impact.
- Event Flow.
- Configuration Impact.
- Security And Privacy Constraints.
- Failure Modes And Recovery.
- Observability And Diagnostics.
- Testing And Verification.
- Rollout And Migration Notes.
- Product Metrics.
- Engineering Acceptance Criteria.
- Product Acceptance Criteria.
- Open Gaps.

Not every document needs every section, but omissions should be intentional.

## Required Sections For Technical Design Documents

A technical design document should include these sections when applicable:

- Context.
- Architectural Decision.
- Alternatives Considered.
- Module Boundary.
- Runtime Flow.
- Sequence Or State Model.
- API Contracts.
- Event Contracts.
- Persistence Contracts.
- Configuration Contracts.
- Security Boundary.
- Operational Behavior.
- Performance Considerations.
- Scalability Considerations.
- Backward Compatibility.
- Migration Strategy.
- Verification Strategy.
- Risks.
- Acceptance Criteria.

A technical design is incomplete if it only names components without defining contracts, ownership, state, and failure handling.

## Required Sections For Product Experience Documents

A product experience document should include these sections when applicable:

- User Roles.
- Task Model.
- Primary Journey.
- Secondary Journeys.
- Entry Points.
- Exit Points.
- Navigation Model.
- Object Model Exposed In UI.
- Permissions In UI.
- Interaction States.
- Error And Recovery UX.
- Empty And First-Run UX.
- Bulk Actions And Safety UX.
- Review And Approval UX.
- Explainability UX.
- Audit And Evidence UX.
- Notification UX.
- Accessibility Requirements.
- Product Metrics.
- Acceptance Criteria.

A product design document is incomplete if it only describes screens without defining task logic, state transitions, permissions, and operational constraints.

## Interaction State Model Requirement

Every user-facing or operator-facing workflow should define interaction states.

Standard states:

- not_configured.
- ready.
- loading.
- validating.
- partially_configured.
- degraded.
- failed.
- permission_denied.
- empty.
- pending_approval.
- running.
- succeeded.
- canceled.
- retrying.
- requires_attention.

Each state should define:

- trigger.
- visible system behavior.
- allowed user actions.
- blocked user actions.
- recovery path.
- telemetry event.
- related backend state.

## Example State Table

| State | Trigger | User Visible Behavior | Allowed Actions | Backend Mapping |
| --- | --- | --- | --- | --- |
| not_configured | connector has no credentials | setup action is primary | configure, cancel | connector.status = pending_configuration |
| validating | user submits connector profile | validation progress is visible | cancel, view logs | automation_job.status = running |
| ready | validation succeeds | connector appears active | test, disable, rotate secret | connector.status = ready |
| degraded | recent checks fail but connector still has cached capability | warning and diagnostics are visible | test, repair, disable | connector.status = degraded |
| failed | validation fails | error and repair hint are visible | edit config, retry validation | connector.status = failed |

## Logical Example Requirement

Every complex feature should include at least one logical example.

A logical example should show:

- initial state.
- actor action.
- command or event.
- module behavior.
- data state change.
- product-visible result.
- audit or observability result.
- failure variant.

## Acceptance Criteria Quality

Acceptance criteria must be verifiable.

Weak criterion:

- The connector should be easy to use.

Strong criterion:

- A workspace admin can register an agent connector by providing only connector type, workspace, and authentication mode. The system generates the connection profile, validates authentication, verifies supported contract versions, runs a health request, registers capabilities, and marks the connector ready only after validation succeeds.

## Documentation Review Checklist

Before a document is considered complete, reviewers should verify:

- the intended professional audience is clear.
- engineering ownership is defined.
- product roles and workflows are defined where relevant.
- contracts and data impact are explicit.
- interaction states are defined for user-facing workflows.
- edge cases and failure modes are documented.
- observability and diagnostics are included.
- tests and acceptance criteria are verifiable.
- unresolved assumptions are linked to gap analysis.
- the document uses precise technical language.

## Acceptance Criteria

This documentation standard is satisfied when:

- new documents are written for professional technical and product readers.
- feature docs include both engineering behavior and product experience behavior.
- technical docs include ownership, contracts, data, state, failure, and verification detail.
- product design docs include roles, workflows, interaction states, permissions, recovery paths, and metrics.
- vague or beginner-level descriptions are replaced with implementation-grade specifications.
