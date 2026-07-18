# Backend Module README Template

Use this template when adding a new backend folder.

```markdown
# Module Name

Path: `backend/path/to/module`

## Purpose

Explain why this module exists.

## Owner

Name the owning team or role when known.

## Modular Boundary

Define what this module owns and what it must not own.

## Public Interfaces

List APIs, events, SDK methods, config schemas, or adapter contracts exposed by this module. If this module exposes HTTP APIs, state how it follows `backend/docs/API_NAMING_AND_CONTRACT_STANDARD.md`.

## Engineering Standards

State how this module follows `backend/docs/ENGINEERING_STANDARDS.md`, including Dependency Injection, ports/adapters, error handling, validation, transactions, idempotency, configuration, observability, and testing seams.

## Dependencies

Allowed dependencies:

- ...

Forbidden dependencies:

- ...

## Testing

Explain required unit, integration, contract, live, or security tests.

## Operational Notes

Document configuration, observability, health checks, and runbook links.

## Status

Draft, scaffold, active, deprecated, or removed.
```
