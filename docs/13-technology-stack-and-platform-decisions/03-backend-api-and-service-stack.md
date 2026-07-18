# 03 - Backend API And Service Stack

## Purpose

This document defines the backend implementation stack for AgentCore services, APIs, workers, SDK generation, validation, and testing.

## Required Stack

| Layer | Technology | Role |
| --- | --- | --- |
| Language | Python | AI workflows, RAG, parsing, automation, backend service implementation |
| API framework | FastAPI | HTTP APIs, OpenAPI generation, async endpoints, dependency wiring at transport boundaries |
| Data validation | Pydantic | request/response validation, config schemas, typed models |
| Database access | SQLAlchemy and Alembic | PostgreSQL access, migrations, transaction handling |
| Testing | pytest | unit, integration, contract, live, and regression tests |
| Static quality | ruff, mypy or pyright | formatting, linting, type checking, import hygiene |
| API contracts | OpenAPI generated from FastAPI | frontend client generation, SDK generation, contract tests |
| Background workers | Python worker services | indexing, embeddings, docs sync, memory consolidation, reporting projections, connector jobs |

## Service Architecture

Backend services must follow the documented layered model:

- domain for entities, value objects, invariants, and pure policies.
- application for use cases, command handlers, query handlers, and port definitions.
- infrastructure for database, broker, filesystem, model provider, parser, and external API adapters.
- interfaces for FastAPI routes, CLI commands, worker consumers, and serializers.
- bootstrap for composition root, dependency wiring, config loading, and startup validation.

## FastAPI Rule

FastAPI should be used at the transport/interface layer. FastAPI dependency features may wire request-scoped concerns, but business logic must not depend on FastAPI objects. Application services must remain framework-independent.

## Python Rule

Python is the primary backend language because AgentCore needs strong support for AI workflows, code parsing, RAG, embeddings, background automation, and integration libraries. Performance-sensitive work should be isolated behind ports and optimized with batching, async IO, workers, or specialized stores before introducing another backend language.

## Dependency Injection Rule

Use explicit Dependency Injection and composition roots. Do not use a global service locator. Infrastructure adapters must be replaceable with fakes in tests.

## API Contract Rule

FastAPI OpenAPI output is a source for TypeScript SDK generation and external SDKs. Contract changes require versioning, examples, contract tests, and release notes.

## Worker Rule

Long-running work must run in background workers, not request handlers. Workers must be idempotent, observable, retry-aware, and dead-letter capable.

## Testing Rule

Backend implementation must include:

- unit tests for domain and application logic.
- integration tests for PostgreSQL, pgvector-backed retrieval, Neo4j, Redis when enabled, object storage, and messaging adapters where relevant.
- contract tests for OpenAPI, events, SDKs, and config schemas.
- live tests for real connectors, model providers, and production-like workflows when required.


## Virtual Environment Policy

All local Python dependency installation must happen inside `/root/AgentCore/.venv`. Backend scripts, tests, tools, workers, generators, and service commands must use the virtual environment unless they run inside an isolated CI or service container.

Global Python package installation is not allowed for normal AgentCore development.

See `06-local-venv-docker-and-port-policy.md` for the full local runtime policy.
