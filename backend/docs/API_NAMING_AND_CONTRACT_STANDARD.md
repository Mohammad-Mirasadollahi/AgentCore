# API Naming And Contract Standard

Path: `backend/docs/API_NAMING_AND_CONTRACT_STANDARD.md`

## Purpose

Defines the backend implementation reference for API naming and contracts.

## Required Reference

All backend APIs must follow `/root/AgentCore/docs/14-api-design-and-naming-standards/`.

## Mandatory Rules

- Use `/api/v1` for public API versioning.
- Use lowercase kebab-case plural resource names.
- Use snake_case JSON wire fields.
- Use explicit DTO names such as CreateTaskRequest and CreateTaskResponse.
- Use IDE pagination for list endpoints.
- Use structured public errors.
- Use Idempotency-Key for retryable POST commands.
- Use stable OpenAPI operation ids.
- Add contract examples and contract tests before implementation is considered complete.

## Status

Documentation standard. No implementation code has been added yet.
