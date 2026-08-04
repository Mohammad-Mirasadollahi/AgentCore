# Live: code-graph-service

## Purpose

Repeatable live probes against a running AgentCore stack (Compose Neo4j/Postgres + MCP HTTP).

## Tests

| File | Requires | What it proves |
| --- | --- | --- |
| `test_unused_candidates_mcp_http_live.py` | MCP HTTP up; `.agentcore/mcp-http.secret` | Ingests tiny fixture into project `deadcode-live`, then proves scored unused_candidates (orphan `old_helper_orphan`) + `kpi_hints` / triage |

## Run

```bash
agentcore service restart   # load current code into MCP HTTP
cd /opt/AgentCore
.venv/bin/python tests/live/code-graph-service/test_unused_candidates_mcp_http_live.py
# or
.venv/bin/python -m pytest tests/live/code-graph-service/test_unused_candidates_mcp_http_live.py -m live -v
```

Artifact: `tests/artifacts/code-graph-live/unused-candidates-live.json`
