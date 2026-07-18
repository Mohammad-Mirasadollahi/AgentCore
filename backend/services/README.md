# Services

Path: `backend/services`

## Purpose

Independently owned backend services.

## Modular Boundary

This directory is part of the AgentCore backend modular architecture. It must expose behavior through documented contracts, public interfaces, configuration, or events. It must not import private internals from sibling modules.

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

Vertical slices are implemented for roadmap and platform services. Canonical tests live under `tests/backend/<service>/` or phase verification folders. See the repository root `README.md` for the phase map.

| Service | Role |
|---------|------|
| `core-data-service` | Phase 1 |
| `memory-service` | Phase 2 |
| `docs-sync-service` | Phase 3 |
| `rule-engine-service` | Phase 4 |
| `adapter-service` | Phase 5 |
| `code-graph-service` | Phase 7 |
| `audit-service` | Audit / evidence trails |
| `identity-access-service` | Identity and authorization |
| `orchestration-service` | Work batches and routing |
| `reporting-service` | Impact / KPI reporting |
| `project-profile-service` | Projects, packs, groups |
| `common-context-service` | Reusable common context items |
