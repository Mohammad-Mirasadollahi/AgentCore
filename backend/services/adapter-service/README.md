# Adapter Service

Path: `backend/services/adapter-service`

## Purpose

Implements Phase 5 interoperability: Universal Agent JSON, connector registry, vendor normalization, in-service pub/sub broker with replay and dead-letter handling, IDE notification delivery, scoped context injection, external tickets, and governed department workflow tasks.

## Modular Boundary

The service owns connectors, adapter mappings, broker events/subscriptions/deliveries/dead letters, external tickets, and department tasks for this vertical slice. It must not read sibling service databases directly.

## Public Interfaces

Documented in `docs/phase-5-api-contract.md`.

## Testing

```bash
PYTHONPATH=backend/services/adapter-service/src .venv/bin/python -m pytest tests/backend/services/adapter-service
```

## Operational Notes

`config/adapter-service.example.env` documents local development settings. Runtime persistence uses the service-owned `adapter` PostgreSQL schema. Broker semantics are co-located for the Phase 5 slice; a later extract to `broker-service` should keep the same contracts.

## Status

Active Phase 5 vertical slice.

LLM calls initiated by AgentCore (when adapters leave stub mode) must use the LiteLLM gateway per `docs/13-technology-stack-and-platform-decisions/09-litellm-llm-gateway.md`.
