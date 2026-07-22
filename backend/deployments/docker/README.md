# Docker

Path: `backend/deployments/docker`

## Purpose

Dockerfile and image build boundaries for AgentCore application containers.

## Status

MCP gateway application image is implemented (`Dockerfile.mcp-gateway`). Infrastructure (Postgres / Neo4j) remains under `backend/deployments/compose/`.

**Normative operator runbook:** [`docs/08-software-engineering-architecture/43-app-docker-and-wheelhouse-runbook.md`](../../../docs/08-software-engineering-architecture/43-app-docker-and-wheelhouse-runbook.md)

## Quick facts (PATH / mounts / CLI)

| Question | Answer |
| --- | --- |
| Does `docker compose up` put `agentcore` on the **host** `PATH`? | **No.** Host PATH still comes from `.venv` / `install.sh`. |
| Can I use the same `agentcore …` operator commands inside the container? | **Partial.** `agentcore version` works via `docker exec`; sync/connect/service orchestration remain host CLI workflows. |
| Is host `.agentcore/` state bind-mounted into `mcp-gateway`? | **No.** Source is copied at image build; DB data lives in Compose named volumes. |
| What clients should use from the host? | MCP HTTP on port `32500` (`/health`, `/mcp`). |

## Wheelhouse (offline deps)

Host `.venv` packages are exported as wheels to `/opt/agentcore-wheelhouse` (override with `AGENTCORE_WHEELHOUSE`):

```bash
bash scripts/build-wheelhouse.sh
```

Images install with `pip install --no-index --find-links=/opt/agentcore-wheelhouse` so the container does not hit PyPI at build time.

## Build and run MCP gateway

```bash
# 1) Export wheels from .venv → /opt/agentcore-wheelhouse
bash scripts/build-wheelhouse.sh

# 2) Build + start app profile (requires core infra healthy)
docker compose --env-file backend/deployments/compose/.env.local \
  -f backend/deployments/compose/compose.yaml \
  --profile core --profile app up -d --build postgres neo4j mcp-gateway
```

Health: `GET http://127.0.0.1:32500/health`  
MCP: `POST http://127.0.0.1:32500/mcp` with `Authorization: Bearer <AGENTCORE_MCP_HTTP_TOKEN>`

Smoke: `bash tests/e2e/docker/run-app-docker-smoke.sh`

## Image And Venv Policy

Local Python dependency installation on the host must use the project `.venv`. Container images install from the `/opt` wheelhouse into an isolated image environment and must not depend on host global Python packages.

Dockerfiles must not hard-code ports, credentials, tenant ids, project ids, model names, provider endpoints, or feature behavior. Runtime configuration must come from environment profiles, compose profiles, or deployment configuration.

## Modular Boundary

This directory is part of the AgentCore backend modular architecture. It must expose behavior through documented contracts, public interfaces, configuration, or events. It must not import private internals from sibling modules.
