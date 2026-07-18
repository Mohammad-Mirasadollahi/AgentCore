# Docker

Path: `backend/deployments/docker`

## Purpose

Dockerfile and image build boundaries.

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

Scaffold only. No implementation code has been added yet.


## Image And Venv Policy

Local Python dependency installation on the host must use `/root/AgentCore/.venv`. Container images should build isolated Python environments inside the image and must not depend on host global Python packages.

Dockerfiles must not hard-code ports, credentials, tenant ids, project ids, model names, provider endpoints, or feature behavior. Runtime configuration must come from environment profiles, compose profiles, or deployment configuration.

Application service containers may be introduced after local `.venv` development workflows are stable. Infrastructure containers are required for normal local development.
