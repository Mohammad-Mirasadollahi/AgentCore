# Typescript

Path: `backend/packages/sdk/typescript`

## Purpose

TypeScript SDK package `@agentcore/sdk` with GET/POST, correlation, and idempotency parity
to Python `agentcore_sdk`.

## Boundaries

- May: public HTTP helpers for AgentCore APIs.
- Must not: embed secret values, import backend service internals.

## Start here

1. `src/client.ts` — `AgentCoreClient`
2. `package.json` — name `@agentcore/sdk`
3. `docs/05-interoperability-ecosystem/11-sdk-release-and-adapter-harness.md`
