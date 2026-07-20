# Application

Path: `backend/services/code-graph-service/src/application`

## Purpose

Service-level scaffold for use-case ownership. Implementation for this service lives under the importable package:

- `backend/services/code-graph-service/src/code_graph_service/application/`

## Modular Boundary

This directory documents the application layer boundary for `code-graph-service`. Runtime application modules are packaged as `code_graph_service.application` (`CodeGraphService` use cases).

## Allowed Contents

- README and design notes for this boundary.
- Cross-links to the packaged application modules.

## Rules

- Application depends on domain ports and models, not concrete stores.
- Infrastructure adapters (`postgres_store`, `neo4j_store`) are selected in bootstrap.

## Status

Active via `code_graph_service.application.service.CodeGraphService`.
