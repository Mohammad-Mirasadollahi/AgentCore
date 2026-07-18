# API Versioning and Contract Governance

## Purpose

AgentCore depends on stable contracts between services, agents, adapters, IDE plugins, CI systems, and external tools. Contract governance prevents hidden breaking changes.

## Contract Types

- HTTP or RPC APIs.
- Broker events.
- Universal Agent JSON messages.
- Database schemas.
- Graph schemas.
- Markdown frontmatter schemas.
- ContextBundle schemas.
- WeightProfile and GraphRetrievalProfile schemas.
- Adapter capability profiles.

## Versioning Rules

- Breaking changes require a new version.
- Additive changes should be backward compatible.
- Consumers must tolerate unknown optional fields.
- Required field changes must go through deprecation period.
- Event schemas must be replay-safe.
- Contract versions must be visible in records and events.

## Deprecation Policy

A deprecated contract should include:

- replacement contract,
- migration guide,
- owner,
- deprecation date,
- removal date,
- affected consumers,
- compatibility guarantees.

## Compatibility Testing

CI should run contract tests for:

- producers against schema,
- consumers against previous versions,
- adapter mappings,
- broker replay,
- frontmatter parsing,
- Universal Agent JSON validation.

## Schema Registry

The platform should maintain a schema registry or equivalent versioned schema catalog. It should include schema owners, versions, status, and compatibility rules.

## Acceptance Criteria

- Every external contract has a version.
- Breaking changes are not released without migration path.
- Contract tests run in CI.
- Deprecated versions are visible and tracked.
- Adapter and broker events are compatible with replay.
