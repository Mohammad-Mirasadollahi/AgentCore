#!/usr/bin/env bash
# Cursor MCP entry: absolute path so spawn PATH does not need nvm/npm on PATH.
# Verbose debug logs -> stderr (Cursor MCP panel) + ai-toolstack/data/mcp-lazy/logs/
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${_SCRIPT_DIR}/../lib/paths.sh"
# shellcheck source=../lib/resolve-node.sh
source "${AI_TOOLSTACK_ROOT}/lib/resolve-node.sh"
# shellcheck source=../lib/mcp-lazy-debug.sh
source "${AI_TOOLSTACK_ROOT}/lib/mcp-lazy-debug.sh"

if ! ensure_node_toolchain; then
  echo "mcp-lazy-serve: node/npx not found (install Node or run ./ai-toolstack/install.sh)" >&2
  exit 127
fi

export PATH="${NODE_TOOLCHAIN_BIN}:${PATH}"

export AI_TOOLSTACK_TOKEN_STATS_DIR="${TOKEN_STATS_DIR}"
export AI_TOOLSTACK_TOKEN_STATS_CJS="${AI_TOOLSTACK_ROOT}/lib/mcp-lazy-token-stats.cjs"
mkdir -p "${AI_TOOLSTACK_TOKEN_STATS_DIR}"

mcp_lazy_log "========== mcp-lazy serve starting =========="
mcp_lazy_log_env
mcp_lazy_log_servers_json || true
mcp_lazy_log_tool_cache
mcp_lazy_enable_node_preload
mcp_lazy_exec_args

mcp_lazy_log "exec: ${MCP_LAZY_CMD[*]} serve $*"
exec "${MCP_LAZY_CMD[@]}" serve "$@"
