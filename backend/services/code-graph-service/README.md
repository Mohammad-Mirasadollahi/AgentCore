# Code Graph Service

Path: `backend/services/code-graph-service`

## Purpose

Owns code graph ingestion, query, graph-backed code context, and metadata-first retrieval for source-read minimization.

## Modular Boundary

This directory is part of the AgentCore backend modular architecture. It must expose behavior through documented contracts, public interfaces, configuration, or events. It must not import private internals from sibling modules.

## Metadata-First Responsibility

This service should build and query compact code metadata before agents read full source files. It should expose context packs with signatures, summaries, dependencies, tests, risk tags, freshness, confidence, and source-read recommendations.

## Allowed Contents

- README and design notes for this boundary.
- Source, configuration, fixtures, tests, or generated artifacts that belong to this boundary.
- Subdirectories that follow the backend structure standard.

## Rules

- Keep ownership clear and local to this boundary.
- Do not hard-code ports, credentials, tenant IDs, project IDs, model names, provider endpoints, or feature behavior.
- Prefer dependency inversion: domain and application logic should not depend on infrastructure implementation details.
- Use shared packages only for stable contracts or cross-cutting primitives.
- Add or update tests and documentation when this boundary receives implementation code.

## Status

Scaffold only. No implementation code has been added yet.
