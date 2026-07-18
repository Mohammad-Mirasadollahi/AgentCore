# Backend Documentation

Path: `backend/docs`

## Purpose

This folder documents the backend structure standard for AgentCore. It is the local reference for creating backend folders, modules, services, packages, integrations, tests, tools, deployments, and runbooks.

## Documents

- `STRUCTURE_STANDARD.md` defines the required backend folder standard, service layout, dependency direction, README standard, naming rules, hard-code prevention, and module creation checklist.
- `MODULE_TEMPLATE.md` provides the README template for new backend modules.
- `NAMING_AND_BOUNDARIES.md` defines naming rules, forbidden vague names, and boundary definition requirements.

## Required Rule

Every backend folder must contain a `README.md`. A folder without a README is considered structurally incomplete.

## Implementation Status

The backend is currently scaffolded with folders and documentation only. No implementation code has been added yet.

- `ENGINEERING_STANDARDS.md` defines mandatory backend implementation standards such as Dependency Injection, ports and adapters, validation, errors, transactions, idempotency, configuration, testing seams, and observability.
- `API_NAMING_AND_CONTRACT_STANDARD.md` defines backend API naming and contract rules and points to the full API standards under `/root/AgentCore/docs/14-api-design-and-naming-standards/`.
