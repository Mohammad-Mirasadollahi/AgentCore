# Backend Engineering Standards

Path: `backend/docs/ENGINEERING_STANDARDS.md`

## Purpose

Defines mandatory implementation standards for AgentCore backend modules. These standards turn software engineering best practices into explicit rules for future code.

## Required Standards

Every backend module must follow:

- Dependency Injection and explicit composition roots.
- Dependency Inversion through ports and adapters.
- Domain logic separated from infrastructure and transport adapters.
- Structured validation and typed error handling.
- Explicit transaction boundaries and idempotency for retryable work.
- Configuration-driven behavior instead of hard-coded runtime values.
- Deterministic clocks, ids, and external dependencies in tests.
- Observability through logs, metrics, traces, health checks, and correlation ids.
- Contract-first APIs and events.
- Secure defaults for authorization, secrets, tenant isolation, and unsafe operations.

## Dependency Injection Rule

Dependencies must be passed explicitly. Domain objects must not know about containers. Application services should receive interfaces through constructors or factories. Infrastructure implementations are selected in bootstrap code.

## Ports And Adapters Rule

Application and domain layers define ports. Infrastructure layers implement adapters. Adapters may depend on provider SDKs, databases, brokers, and filesystem APIs. Domain and application layers must not depend on those details.

## Error Handling Rule

Expected failures must use typed errors or Result-style responses. Unexpected failures must preserve diagnostics while avoiding secret leakage.

## Testing Rule

Every module must expose test seams through public contracts, ports, fake adapters, and deterministic primitives. Tests must not rely on private internals unless the test explicitly targets a private algorithm inside the same module.

## Review Rule

A code review must reject code that introduces service locator behavior, hidden hard-coded runtime settings, direct cross-service database access, unbounded retries, unstructured errors, or infrastructure dependencies inside domain logic.
