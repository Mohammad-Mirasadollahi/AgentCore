# Neo4j Python ingest acceptance gate

Runs live/parity/hybrid pytest targets for `code-graph-service` against Compose Neo4j + Postgres on non-default ports.

```bash
# Optional: wait with hard timeout first
backend/deployments/compose/wait-healthy.sh --timeout 90 agentcore-neo4j-1 agentcore-postgres-1

# Soft gate (skips reachability if down; pytest skips live tests)
.venv/bin/python tests/backend/gates/neo4j-python-ingest/run_gate.py

# Strict gate (fail if ports down)
.venv/bin/python tests/backend/gates/neo4j-python-ingest/run_gate.py --require-live --json
```

Environment defaults match the AgentCore port profile (`32287` Bolt, `32232` Postgres).
