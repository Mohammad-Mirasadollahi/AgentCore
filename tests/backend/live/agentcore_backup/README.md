# Live: project-scoped backup / restore

Requires Compose Postgres (and Neo4j when graph store is neo4j).

```bash
cd /opt/AgentCore
.venv/bin/python -m pytest tests/backend/live/agentcore_backup -m live -q
```
