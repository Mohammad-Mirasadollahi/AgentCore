# 05 - Modular Project Structure

## Purpose

This document defines the recommended modular project structure for AgentCore from a Software Engineering perspective. It explains how the repository should be organized, how modules should depend on each other, where each type of code should live, and how engineers should extend the system without creating hidden coupling.

This document is intentionally implementation-oriented. A developer should be able to use it as the first reference when creating folders, packages, services, shared libraries, tests, configuration files, migrations, or operational tooling.

## Architectural Decision

AgentCore should start as a modular monorepo.

The monorepo is recommended because the early system contains many tightly related contracts: activities, work logs, decisions, tasks, memory objects, documentation anchors, graph entities, rule events, broker messages, and adapter payloads. Keeping these contracts in one repository reduces drift while the product model is still evolving.

The repository must still be modular. A monorepo is not permission to create a shared codebase without boundaries. Each service owns its domain model, use cases, persistence adapters, tests, migrations, and runtime entrypoints. Shared packages are allowed only for stable contracts, infrastructure helpers, SDKs, test utilities, and cross-cutting platform primitives.

A future multi-repo split is possible only after service contracts become stable and independent release cadence becomes valuable.

## Top-Level Project Tree

The recommended project tree is:

    AgentCore/
      apps/
        api-gateway/
        admin-console/
        ide-extension/
        cli/
      services/
        core-data-service/
        memory-service/
        docs-sync-service/
        code-graph-service/
        rule-engine-service/
        broker-service/
        adapter-service/
        config-service/
        audit-service/
      packages/
        contracts/
        domain-events/
        sdk/
        auth/
        config/
        observability/
        persistence/
        queueing/
        validation/
        testkit/
      infra/
        docker/
        compose/
        kubernetes/
        terraform/
        migrations/
        local-dev/
      docs/
        00-master-plan/
        01-core-data-model/
        02-memory-and-context/
        03-docs-as-code-sync/
        04-rule-engine-orchestration/
        05-interoperability-ecosystem/
        06-technical-logic/
        07-code-knowledge-graph/
        08-software-engineering-architecture/
        09-platform-governance-operations/
        10-gap-analysis/
        11-logical-implementation-examples/
      scripts/
        dev/
        ci/
        release/
        maintenance/
      tools/
        port-preflight/
        schema-registry/
        graph-inspector/
        migration-runner/
        docs-validator/
      tests/
        integration/
        contract/
        e2e/
        performance/
        fixtures/
      examples/
        agent-workflows/
        adapter-payloads/
        memory-retrieval/
        docs-sync/
      .github/
        workflows/
      README.md

## Top-Level Folder Responsibilities

### apps

The apps folder contains user-facing or operator-facing applications. Apps may call services through APIs, SDKs, or event subscriptions, but they must not import service internals.

Expected apps:

- api-gateway exposes the external HTTP or RPC surface for agents, IDE tools, admin screens, and automation clients.
- admin-console provides operational views for work logs, tasks, memory, rules, gaps, graph health, and system status.
- ide-extension integrates AgentCore with development environments and sends structured context events.
- cli provides local developer and operator commands such as validation, import, export, diagnostics, and preflight checks.

Apps own presentation logic, user workflows, command parsing, and API composition. They do not own core domain rules.

### services

The services folder contains independently deployable or independently testable backend modules. Each service owns one bounded context.

Expected services:

- core-data-service owns Activity, WorkLog, Decision, Issue, Task, relations, lifecycle transitions, and audit-safe persistence.
- memory-service owns memory tiers, retrieval scoring, weight calculation, consolidation, decay, summarization, and context assembly.
- docs-sync-service owns docs-as-code synchronization, frontmatter validation, document anchors, document graph metadata, and documentation drift detection.
- code-graph-service owns repository ingestion, Tree-sitter parsing, symbol extraction, Neo4j graph writes, impact queries, and graph-guided code context.
- rule-engine-service owns semantic rules, anomaly detection, policy execution, escalation logic, and automated routing decisions.
- broker-service owns Pub/Sub contracts, event routing, retries, dead-letter handling, idempotency keys, and replay boundaries.
- adapter-service owns vendor adapters, Universal Agent JSON conversion, provider capability mapping, and external tool integration.
- config-service owns configuration profiles, feature flags, environment policies, runtime settings, and port allocation records.
- audit-service owns immutable audit streams, retention policies, compliance exports, and evidence queries.
- common-context-service owns reusable project guidance, repeated-instruction proposals, common item lifecycle, bundle resolution, scoring, conflict detection, and reuse reporting.

A service may be deployed as a process, container, or logical module depending on project maturity. The boundary still exists even when multiple services run in one process during early development.

### packages

The packages folder contains shared libraries that are stable enough to be reused. Shared packages must stay small and boring. They should not become a place for business logic that no team wants to own.

Expected packages:

- contracts contains API schemas, event schemas, DTO definitions, and versioned public types.
- domain-events contains canonical event names, event envelopes, causality metadata, correlation IDs, and idempotency primitives.
- sdk contains typed clients for apps, agents, tools, and external integrations.
- auth contains authentication and authorization primitives that are used consistently by services and apps.
- config contains typed config loading, config validation, environment profile resolution, and no-hard-code guards.
- observability contains logging, tracing, metrics, span names, health check helpers, and structured diagnostic fields.
- persistence contains database connection helpers, transaction wrappers, migration interfaces, and repository base primitives.
- queueing contains broker clients, retry helpers, dead-letter helpers, and message acknowledgement utilities.
- validation contains schema validation helpers and common error formats.
- testkit contains builders, fake adapters, contract test harnesses, integration fixtures, and deterministic time utilities.
- common-context contains reusable common item contracts, resolver interfaces, templates, and examples so repeated guidance is centralized instead of duplicated across services.

Shared packages may depend on other shared packages only when the dependency direction is stable and explicitly documented.

### infra

The infra folder contains deployment and infrastructure definitions. It must not contain application business logic.

Expected areas:

- docker contains image definitions and base runtime images.
- compose contains local orchestration profiles.
- kubernetes contains deployment, service, ingress, secret reference, and autoscaling manifests.
- terraform contains cloud or infrastructure provisioning definitions.
- migrations contains database and graph migration assets when they are shared across services.
- local-dev contains local bootstrap profiles, development-only overrides, and generated port maps.

Development ports must not use framework defaults. Local port values must be configurable, documented, and validated before services start.

### docs

The docs folder is the source of truth for architecture, design, logic, risk, operations, and implementation examples. It must remain indexed and phase-oriented.

Every major module should link back to relevant docs. For example, memory-service should reference the memory architecture, memory technical logic, and logical retrieval examples.

### scripts

The scripts folder contains automation scripts for development, CI, release, and maintenance. Scripts must be repeatable and should fail clearly when prerequisites are missing.

Scripts should call tools and service commands. They should not contain hidden business rules.

### tools

The tools folder contains engineer-facing utilities that support the repository.

Expected tools:

- port-preflight validates that configured development ports do not conflict with local services or reserved ranges.
- schema-registry validates contract schemas, event versions, and compatibility rules.
- graph-inspector checks graph ingestion health, orphan symbols, stale references, and missing anchors.
- migration-runner executes service migrations in a controlled order.
- docs-validator checks indexes, links, required metadata, and documentation completeness.

### tests

The tests folder contains cross-module tests. Service-owned unit tests and service integration tests stay inside each service. Repository-level tests cover system behavior across boundaries.

Expected test groups:

- integration verifies service-to-service flows.
- contract verifies API and event compatibility.
- e2e verifies complete user and agent workflows.
- performance verifies ingestion, retrieval, graph query, and broker throughput targets.
- fixtures contains reusable test data and scenario payloads.

### examples

The examples folder contains realistic usage examples that developers can run or inspect. Examples should use public contracts, SDKs, and documented configuration instead of service internals.

## Standard Service Layout

Each backend service should follow this internal structure:

    services/<service-name>/
      README.md
      docs/
        design-notes.md
        operational-notes.md
      src/
        api/
          controllers/
          routes/
          serializers/
        application/
          commands/
          queries/
          handlers/
          workflows/
        domain/
          entities/
          value-objects/
          policies/
          services/
          events/
        infrastructure/
          persistence/
          messaging/
          external-clients/
          configuration/
          observability/
        workers/
          consumers/
          scheduled-jobs/
          projectors/
        bootstrap/
          dependency-injection/
          service-startup/
      tests/
        unit/
        integration/
        contract/
        fixtures/
      migrations/
      config/
        development.example.yaml
        test.example.yaml
        production.example.yaml
      package-manifest

The exact file names may change based on implementation language and framework, but the boundaries should remain stable.

## Layering Rules Inside a Service

A service should be organized around clean dependency direction.

Allowed dependency direction:

    api -> application -> domain
    workers -> application -> domain
    infrastructure -> application or domain through interfaces
    bootstrap -> api, workers, infrastructure, application

Domain rules:

- The domain layer contains business concepts and invariants.
- The domain layer does not know about HTTP, databases, brokers, filesystems, frameworks, or environment variables.
- Domain events are created by domain logic but published by application or infrastructure code.
- Domain policies should be deterministic and easy to test.

Application rules:

- The application layer contains use cases and orchestration logic.
- Commands change state and should emit events when important state changes occur.
- Queries read state and should not create side effects.
- Application handlers coordinate repositories, domain services, event publishing, and authorization checks.

API rules:

- The API layer translates external requests into application commands or queries.
- API code validates transport-level shape and authentication context.
- API code should not contain domain decisions.

Infrastructure rules:

- Infrastructure implements repositories, broker clients, graph clients, external tool clients, config loaders, and observability exporters.
- Infrastructure adapts external systems to internal interfaces.
- Infrastructure code may be replaced without rewriting domain logic.

Worker rules:

- Workers consume events, run scheduled jobs, update projections, and perform long-running tasks.
- Workers should be idempotent because broker retries are expected.
- Workers should record causality metadata for audit and replay.

## Example: Memory Service Layout

The memory-service should be structured as follows:

    services/memory-service/
      src/
        api/
          controllers/
            retrieve-context-controller
            memory-feedback-controller
          serializers/
            memory-response-serializer
        application/
          commands/
            consolidate-memory-command
            record-memory-feedback-command
          queries/
            retrieve-context-query
            explain-memory-ranking-query
          handlers/
            retrieve-context-handler
            consolidate-memory-handler
            record-memory-feedback-handler
          workflows/
            build-agent-context-workflow
        domain/
          entities/
            memory-item
            memory-cluster
            context-window
          value-objects/
            memory-weight
            recency-score
            relevance-score
            confidence-score
          policies/
            retention-policy
            decay-policy
            retrieval-policy
          services/
            memory-ranker
            memory-consolidator
            context-budgeter
          events/
            memory-recorded-event
            memory-consolidated-event
            memory-feedback-recorded-event
        infrastructure/
          persistence/
            memory-repository
            memory-cluster-repository
          messaging/
            memory-event-publisher
            activity-event-consumer
          external-clients/
            embedding-client
            summarization-client
          configuration/
            memory-config-loader
            ranking-weight-config
          observability/
            memory-metrics
            retrieval-tracing
        workers/
          consumers/
            activity-memory-consumer
          scheduled-jobs/
            memory-decay-job
            memory-consolidation-job
          projectors/
            memory-usage-projector

Important implementation logic:

- Retrieval must combine multiple configurable weights, not a hard-coded score.
- Weight factors should include relevance, recency, confidence, source quality, user feedback, task similarity, project similarity, and risk sensitivity.
- The scoring formula must be config-driven and versioned so experiments can be audited.
- The service should return an explanation of why each memory item was selected.
- Memory output should include enough metadata for downstream agents to decide whether to trust or ignore an item.

## Example: Code Graph Service Layout

The code-graph-service should be structured as follows:

    services/code-graph-service/
      src/
        api/
          controllers/
            graph-query-controller
            impact-analysis-controller
        application/
          commands/
            ingest-repository-command
            refresh-symbol-command
          queries/
            find-symbol-query
            explain-impact-query
            retrieve-code-context-query
          handlers/
            ingest-repository-handler
            explain-impact-handler
            retrieve-code-context-handler
        domain/
          entities/
            repository
            source-file
            symbol
            code-edge
            graph-snapshot
          value-objects/
            symbol-id
            file-anchor
            graph-version
          policies/
            ingestion-policy
            stale-edge-policy
          services/
            symbol-resolver
            impact-analyzer
            graph-context-selector
          events/
            repository-ingested-event
            symbol-changed-event
            graph-snapshot-created-event
        infrastructure/
          persistence/
            neo4j-symbol-repository
            graph-snapshot-repository
          external-clients/
            tree-sitter-parser-client
            git-client
          messaging/
            code-graph-event-publisher
          configuration/
            parser-config-loader
            graph-database-config
        workers/
          consumers/
            repository-change-consumer
          scheduled-jobs/
            graph-health-check-job
          projectors/
            documentation-link-projector

Important implementation logic:

- Parsing must be incremental when possible.
- Graph writes must be idempotent and versioned.
- Symbol IDs must be stable across repeated ingestion when the code did not semantically change.
- Impact analysis must return both direct and transitive dependencies.
- Graph context selection should prefer exact symbols, then related files, then documented decisions, then recent work logs.

## Dependency Rules Between Modules

The dependency rules are:

- Apps may depend on packages and public service APIs.
- Apps must not import service internal source files.
- Services may depend on packages.
- Services must not import another service internal source files.
- Services communicate through APIs, events, shared contracts, or SDK clients.
- Packages must not depend on services or apps.
- Infra must not depend on application code.
- Tests may use testkit and public module interfaces.
- Contract tests may import schemas from packages/contracts.

Invalid examples:

- memory-service importing core-data-service repository classes directly.
- admin-console reading a service database table directly.
- docs-sync-service writing Neo4j records without going through code-graph-service or a documented graph contract.
- rule-engine-service importing API controllers from api-gateway.
- shared packages containing service-specific business decisions.

Valid examples:

- memory-service consuming ActivityCreated events from broker-service.
- rule-engine-service publishing EscalationRequested events through domain-events contracts.
- admin-console calling api-gateway endpoints.
- code-graph-service exposing impact analysis through an API and event stream.
- docs-sync-service using contracts from packages/contracts to validate documentation anchor events.

## Contract Ownership

Contracts are public promises. Every API schema, event schema, and adapter schema must have an owner.

Ownership rules:

- The service that produces an event owns the event schema.
- The service that exposes an API owns the API contract.
- packages/contracts stores the versioned shared copy of public contracts.
- Breaking changes require a migration plan and compatibility window.
- Contract tests must verify both producers and consumers.
- Deprecated fields must remain documented until fully removed.

Contract files should include:

- name
- version
- owner
- lifecycle state
- compatibility notes
- required fields
- optional fields
- validation rules
- example payload
- error behavior

## Configuration Structure

Configuration must be explicit, typed, validated, and environment-aware.

Recommended configuration layout:

    services/<service-name>/config/
      development.example.yaml
      test.example.yaml
      production.example.yaml
    infra/local-dev/
      ports.example.yaml
      services.example.yaml
    packages/config/
      src/
        config-loader
        schema-validator
        environment-profile
        secret-reference

Configuration rules:

- No service should hard-code hostnames, ports, credentials, database names, topic names, retention values, scoring weights, or feature flags.
- Development port values must be changed away from framework defaults.
- Port allocation should be stored in a local-dev config profile and validated by port-preflight before startup.
- Secrets must be referenced through secret providers or environment references, not committed as literal values.
- Runtime config should expose effective values in diagnostic mode without printing secrets.

## Development Port Strategy

Port conflict prevention is part of the architecture.

Default framework ports should not be used during development. For example, common defaults such as 3000, 5000, 5173, 5432, 6379, 7474, 7687, 8000, 8080, and 9090 should be treated as reserved or avoided unless the team explicitly configures otherwise.

AgentCore development should use a documented non-default range. Example allocations are defined in the port management document and should remain configurable:

- api-gateway: 32100
- admin-console: 32101
- core-data-service: 32110
- memory-service: 32120
- docs-sync-service: 32130
- code-graph-service: 32140
- rule-engine-service: 32150
- broker-service: 32160
- adapter-service: 32170
- config-service: 32180
- neo4j-http: 32287
- neo4j-bolt: 32474
- redis-compatible-cache: 32333
- observability-dashboard: 32390

These values are examples, not hard-coded constants. The effective values must come from config files, environment profiles, or generated local development settings.

## Testing Structure

Testing should follow module boundaries.

Service-level tests:

- unit tests validate domain policies, value objects, application handlers, and pure logic.
- integration tests validate service persistence, broker interactions, graph clients, and external adapters through controlled fixtures.
- contract tests validate API and event compatibility.

Repository-level tests:

- integration tests validate cross-service workflows such as activity creation to memory retrieval.
- e2e tests validate complete user-visible flows such as IDE event to task routing to documentation update.
- performance tests validate graph ingestion, memory retrieval, broker replay, and rule execution throughput.

Testing rules:

- Domain tests must not require databases or brokers.
- Contract tests must run before integration tests.
- E2E tests should use public APIs and public event contracts.
- Fixtures should be realistic and versioned.
- Test data should include failure and edge cases, not only happy paths.

## Module Ownership Matrix

Ownership should be explicit even before teams are assigned.

| Module | Primary Responsibility | Main Consumers | Stability Level |
| --- | --- | --- | --- |
| api-gateway | External API composition and request entry | apps, agents, CLI, IDE tools | medium |
| admin-console | Operator and reviewer UI | human users | medium |
| core-data-service | Activity, WorkLog, Decision, Issue, Task | all platform services | high |
| memory-service | retrieval, weighting, consolidation, context assembly | agents, api-gateway, rule-engine | high |
| docs-sync-service | docs-as-code, anchors, drift detection | developers, code-graph, rule-engine | medium |
| code-graph-service | repository graph, symbols, impact analysis | agents, docs-sync, rule-engine | high |
| rule-engine-service | policy execution, routing, anomaly detection | core-data, broker, admin-console | high |
| broker-service | event routing, retries, replay | all services | high |
| adapter-service | provider and tool integration | external agents, IDE tools | medium |
| config-service | profiles, feature flags, runtime settings | all services | high |
| audit-service | immutable evidence and compliance export | admin-console, governance | high |
| packages/contracts | public schemas and DTOs | all modules | very high |
| packages/testkit | test support only | tests | low |

## Naming Conventions

Naming should make boundaries obvious.

Folder naming:

- top-level folders use plural nouns where they contain collections.
- services use kebab-case and end with service.
- packages use short nouns that describe reusable capability.
- tests use names that describe behavior, not only implementation details.

Domain naming:

- entity names should match documented concepts such as Activity, WorkLog, Decision, Issue, Task, MemoryItem, CodeSymbol, Rule, AdapterCapability, and AuditRecord.
- event names should be past-tense facts such as ActivityCreated, MemoryConsolidated, RuleViolated, DocumentationDriftDetected, and CodeGraphSnapshotCreated.
- command names should be imperative requests such as CreateTask, RecordDecision, RetrieveContext, IngestRepository, and EvaluateRules.
- query names should describe read intent such as GetTaskTimeline, FindRelatedMemories, ExplainImpact, and ListOpenGaps.

## Build and Release Boundaries

Each service and package should be independently buildable and testable.

Build expectations:

- A change inside one service should run that service tests and affected contract tests.
- A change inside packages/contracts should run all affected producer and consumer contract tests.
- A change inside packages/config or packages/observability should run all services that depend on it.
- A documentation-only change should run docs validation and link checks.
- A migration change should run migration validation and rollback checks where rollback is supported.

Release expectations:

- Public contracts are versioned.
- Runtime services expose health and readiness checks.
- Deployment artifacts identify the service name, version, git revision, config profile, and contract version set.
- Release notes must mention contract changes, migrations, port changes, and operational risks.

## Documentation Rules For Modules

Every service should include a README.md with:

- purpose
- owned domain concepts
- public APIs
- produced events
- consumed events
- dependencies
- configuration keys
- port configuration behavior
- persistence stores
- operational metrics
- failure modes
- local development commands
- test commands
- links to architecture docs

Every shared package should include a README.md with:

- purpose
- public API surface
- allowed consumers
- forbidden consumers
- versioning policy
- examples
- compatibility rules

## Anti-Patterns To Avoid

The project should actively avoid these patterns:

- shared domain model imported by every service without ownership.
- business logic inside API controllers.
- service-to-service database access.
- hard-coded ports, hostnames, credentials, topic names, model names, scoring weights, or feature flags.
- one global utilities package that grows without review.
- adapter code mixed into core domain services.
- tests that pass only because they use private internals.
- documentation that describes desired behavior but does not map to modules, contracts, or tests.
- graph writes from multiple services without a single ownership contract.
- memory retrieval scores that cannot be explained or tuned.

## Implementation Workflow For New Modules

When adding a new module, engineers should follow this workflow:

1. Identify the bounded context and owner.
2. Add the service or package folder under the correct top-level directory.
3. Write the module README before writing production code.
4. Define public contracts in packages/contracts when the module exposes APIs or events.
5. Add configuration schema and example environment profiles.
6. Add development port entries when the module opens a port.
7. Add domain tests for pure rules.
8. Add contract tests for public APIs and events.
9. Add integration tests for persistence, brokers, graph stores, or external tools.
10. Link the module README to the relevant documentation section.
11. Update docs indexes when the module introduces a new architectural area.
12. Run docs validation, contract tests, and affected service tests.

## Acceptance Criteria

The modular project structure is acceptable when:

- A new engineer can locate the correct folder for an app, service, package, tool, script, test, or infrastructure asset.
- No service imports another service internal implementation.
- Shared packages contain stable reusable primitives, not unowned business logic.
- Every public contract has an owner, version, examples, and tests.
- Every service has clear domain, application, API, infrastructure, worker, test, config, and migration boundaries.
- Development ports are configurable and validated before startup.
- Documentation links modules to architecture, logic, operations, and examples.
- Gaps and unresolved ownership questions are recorded in the gap-analysis section instead of being hidden in code.


## Current Backend Scaffold Reference

The live backend scaffold is located at `/root/AgentCore/backend`.

Backend folder creation must follow:

- `/root/AgentCore/backend/README.md`
- `/root/AgentCore/backend/docs/STRUCTURE_STANDARD.md`
- `/root/AgentCore/backend/docs/MODULE_TEMPLATE.md`
- `/root/AgentCore/backend/docs/NAMING_AND_BOUNDARIES.md`

The current scaffold is intentionally documentation-first. It creates modular boundaries, service ownership areas, shared package boundaries, platform adapters, integration areas, configuration profiles, deployments, tests, tools, and runbooks before implementation code is added.

Every backend folder must include a README that states purpose, modular boundary, allowed contents, rules, and status. Future implementation work should update these README files instead of adding undocumented source folders.


## Common Context Reuse Structure

AgentCore must include a first-class Common Context area so stable project rules and definitions do not need to be repeated in every user request, agent run, ticket, or workflow.

Required folders:

    backend/domains/common-context/
      model/
      policies/
      events/
      use-cases/
      examples/
    backend/services/common-context-service/
      src/
      tests/
      docs/
      migrations/
      config/
    backend/packages/common-context/
      contracts/
      resolvers/
      templates/
      examples/
    backend/configs/common-context-profiles/

The common-context domain defines vocabulary and policy. The common-context-service owns lifecycle and resolution. The common-context package exposes reusable contracts and deterministic resolver primitives. The common-context-profiles directory keeps score weights, token budgets, approval thresholds, and feature toggles out of code.

Common context must be project-scoped by default. Cross-project reuse is allowed only through explicit project-group composition and audit records.


## Engineering Standards Structure

Backend implementation must follow `/root/AgentCore/backend/docs/ENGINEERING_STANDARDS.md` and the Software Engineering Architecture standards in files 29 through 33.

Shared cross-cutting primitives should live under:

    backend/packages/shared-kernel/dependency-injection/
    backend/packages/shared-kernel/validation/
    backend/packages/shared-kernel/results/
    backend/packages/shared-kernel/time/
    backend/packages/shared-kernel/resilience/
    backend/packages/shared-kernel/testing/

These folders are for stable primitives only. They must not become a dumping ground for business logic.
