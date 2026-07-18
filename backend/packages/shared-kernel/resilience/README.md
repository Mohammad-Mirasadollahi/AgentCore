# Resilience Primitives

Path: `backend/packages/shared-kernel/resilience`

## Purpose

Defines future retry, timeout, circuit breaker, backoff, bulkhead, and idempotency helper primitives.

## Rules

Retries must be bounded, observable, and idempotency-aware. Infrastructure resilience must not hide business failures.
