#!/usr/bin/env bash
# Source from bin/headroom-mcp-serve.sh and install.sh — do not export globally.
#
# Headroom MCP (via mcp-lazy): compress / retrieve / stats for large blobs
# (JSON, logs, files, RAG). Optional proxy mode — see docs/headroom-integration.md.

: "${HEADROOM_DIR:=${AI_TOOLSTACK_DATA}/headroom}"

export HEADROOM_WORKSPACE_DIR="${HEADROOM_DIR}"
export HEADROOM_TELEMETRY=off
export HEADROOM_UPDATE_CHECK=off
export HEADROOM_STATELESS=false

# Disk-first file reads via headroom_read (avoid cat → terminal for large logs).
export HEADROOM_MCP_READ=on

# Optional proxy for LLM-level compression (advanced — see docs/headroom-integration.md).
# When unset, headroom_retrieve uses the local CompressionStore (MCP-only mode).
# export HEADROOM_PROXY_URL=http://127.0.0.1:8787

load_headroom_env() {
  # shellcheck disable=SC1090
  [[ -f "${HEADROOM_ENV_SH:-}" ]] && source "${HEADROOM_ENV_SH}"
}
