#!/usr/bin/env bash
# MCP gateway container entrypoint — normalize DB hosts for Compose DNS.
set -euo pipefail

# When Compose injects service hostnames, prefer them over host-loopback URLs.
if [[ -n "${AGENTCORE_POSTGRES_HOST:-}" && -n "${AGENTCORE_POSTGRES_PASSWORD:-}" ]]; then
  pg_user="${AGENTCORE_POSTGRES_USER:-agentcore}"
  pg_db="${AGENTCORE_POSTGRES_DATABASE:-agentcore}"
  pg_host="${AGENTCORE_POSTGRES_HOST}"
  pg_port="${AGENTCORE_POSTGRES_PORT:-5432}"
  export AGENTCORE_DATABASE_URL="postgresql://${pg_user}:${AGENTCORE_POSTGRES_PASSWORD}@${pg_host}:${pg_port}/${pg_db}"
  export AGENTCORE_MCP_STORE_MODE="${AGENTCORE_MCP_STORE_MODE:-postgres}"
fi

if [[ -n "${AGENTCORE_NEO4J_HOST:-}" ]]; then
  neo_user="${AGENTCORE_NEO4J_USER:-neo4j}"
  neo_port="${AGENTCORE_NEO4J_BOLT_PORT:-7687}"
  export AGENTCORE_NEO4J_URI="bolt://${AGENTCORE_NEO4J_HOST}:${neo_port}"
  export AGENTCORE_NEO4J_USER="${neo_user}"
  export AGENTCORE_CODE_GRAPH_STORE="${AGENTCORE_CODE_GRAPH_STORE:-neo4j}"
  export AGENTCORE_MCP_GRAPH_MODE="${AGENTCORE_MCP_GRAPH_MODE:-neo4j}"
fi

if [[ -z "${AGENTCORE_MCP_TOKEN_SECRET:-}" && -z "${AGENTCORE_MCP_HTTP_TOKEN:-}" ]]; then
  export AGENTCORE_MCP_HTTP_TOKEN="${AGENTCORE_MCP_HTTP_TOKEN:-agentcore-docker-dev-token}"
fi

export AGENTCORE_ROOT="${AGENTCORE_ROOT:-/opt/AgentCore}"
export AGENTCORE_MCP_HTTP_HOST="${AGENTCORE_MCP_HTTP_HOST:-0.0.0.0}"
export AGENTCORE_MCP_HTTP_PORT="${AGENTCORE_MCP_HTTP_PORT:-32500}"

exec "$@"
