# Runtime and Deployment Architecture

## Purpose

This document defines how AgentCore should run across development, staging, and production. The system should be configurable, observable, and safe to run alongside other tools without port conflicts.

## Runtime Topology

A typical deployment contains:

- API Gateway
- Core Data Service
- Memory Service
- Documentation Sync Service
- Code Graph Service
- Rule Engine Service
- Broker Service
- Adapter Service
- Admin and Configuration Service
- Background Workers
- PostgreSQL with pgvector
- Neo4j-backed code graph tables
- PostgreSQL full-text and fuzzy search
- Object/artifact storage
- Observability stack

## Environment Types

### Development

Development must prioritize local ergonomics and port safety. Ports should be non-default, project-scoped, and overrideable by environment variables or a local config file.

### Staging

Staging should mirror production service topology but use isolated data, isolated broker topics, isolated secrets, and explicit test tenants.

### Production

Production must use managed secrets, hardened network boundaries, stable service discovery, health checks, metrics, tracing, and capacity planning.

## Configuration Model

Configuration should be layered:

1. platform defaults,
2. environment defaults,
3. tenant settings,
4. project settings,
5. local developer overrides,
6. runtime secrets.

No service should require source-code changes to change ports, hostnames, model routing, profile weights, broker topics, or database endpoints.

## Service Discovery

Production should use service discovery, internal DNS, or orchestration-native service names. Development can use local hostnames and port profiles, but those profiles must avoid common defaults and be documented.

## Health Checks

Every service should expose:

- liveness check,
- readiness check,
- dependency check,
- version endpoint,
- configuration profile summary without secrets.

## Observability

Every request, job, message, graph update, memory retrieval, rule evaluation, and model call should carry a correlation ID.

Required signals:

- request latency,
- job duration,
- queue depth,
- retry count,
- dead-letter count,
- model call count,
- token usage,
- graph indexing duration,
- memory retrieval score distribution,
- port allocation failures in development.

## Deployment Constraints

- Development ports must not use common defaults unless explicitly overridden.
- Port values must be configuration, not constants.
- Services must fail with clear messages when required ports are unavailable.
- Workers must be horizontally scalable.
- Long-running jobs must be resumable or idempotent.
- Schema migrations must be versioned and reversible where possible.


## Technology Baseline

Runtime implementation should align with `../13-technology-stack-and-platform-decisions/`.

Baseline runtime technologies:

- Next.js and TypeScript for the admin console.
- Python and FastAPI for backend APIs and services.
- PostgreSQL with pgvector for primary transactional records and RAG/vector storage.
- Neo4j for code graph traversal, PostgreSQL for metadata/reporting aggregates/analytics projections, and Redis for optional ephemeral cache or coordination.
- Neo4j is required for the code graph. Redis is enabled when ephemeral cache, coordination, locks, rate limits, or short-lived job state are needed. Do not add another product for an already assigned role without a formal ADR.
- S3-compatible object storage for evidence bundles, exports, diagnostics, and large artifacts.
- OpenTelemetry-compatible observability for traces, metrics, logs, and correlation ids.


## Local Runtime Isolation Policy

AgentCore local development must isolate Python dependencies in `/root/AgentCore/.venv`. PostgreSQL, Neo4j, Redis, and supporting infrastructure must run through Docker Compose profiles or equivalent container orchestration. Object storage and observability components may run through profiles when enabled.

Newly exposed development host ports must not use vendor defaults. Existing configured ports should not be changed unless an explicit migration is requested. PostgreSQL is the only required local database service.

See `../13-technology-stack-and-platform-decisions/06-local-venv-docker-and-port-policy.md` for the complete policy.
