# Production retrieval live tests

Saved live suite for BM25 / FTS / explore / architecture / GDS-option / APOC /
routes / TESTED_BY against Compose Neo4j + Postgres (non-default ports).

Normative runbook:
[`docs/07-code-knowledge-graph/33-production-retrieval-live-test-gates.md`](../../../docs/07-code-knowledge-graph/33-production-retrieval-live-test-gates.md)

## Prerequisites

```bash
backend/deployments/compose/wait-healthy.sh --timeout 90 agentcore-neo4j-1 agentcore-postgres-1
```

## Run

```bash
export AGENTCORE_NEO4J_PASSWORD=agentcore-local-dev-secret
export AGENTCORE_POSTGRES_PASSWORD=agentcore-local-dev-secret
# optional:
# export AGENTCORE_NEO4J_GDS_ENABLED=true
# export AGENTCORE_NEO4J_GDS_CONCURRENCY=4

PYTHONPATH=backend/services/code-graph-service/src \
  .venv/bin/python -m pytest \
  tests/backend/services/code-graph-service/test_production_retrieval_live.py -v
```

JSON artifacts land in `tests/artifacts/code-graph-live/`.

## Cases

| Kind | Test |
| --- | --- |
| Simple | capabilities + GDS flag/concurrency |
| Simple | ingest → hybrid → explore |
| Simple | path + architecture + freshness |
| Challenge | RRF prefers auth over UI noise |
| Challenge | FastAPI routes + TESTED_BY + detect_changes |
| Challenge | two call clusters + neighbors/degree |
| Challenge | GDS disabled → cypher.degree only |
| Challenge | Postgres FTS + hybrid |
| Challenge | write live JSON artifact |
