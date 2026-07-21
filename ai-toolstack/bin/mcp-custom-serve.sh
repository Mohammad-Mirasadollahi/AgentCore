#!/usr/bin/env bash
# Verbose wrapper for custom/personal MCP backends behind mcp-lazy.
# Usage in ~/.mcp-lazy/servers.json:
#   "my-server": {
#     "command": "/path/to/ai-toolstack/bin/mcp-custom-serve.sh",
#     "args": ["/path/to/your/mcp/entry", "optional-arg"],
#     "cwd": "/path/to/project",
#     "env": { "MY_VAR": "value" }
#   }
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${_SCRIPT_DIR}/../lib/paths.sh"

MCP_CUSTOM_LOG_DIR="${MCP_LAZY_LOG_DIR:-${AI_TOOLSTACK_DATA}/mcp-lazy/logs}/backends"
mkdir -p "${MCP_CUSTOM_LOG_DIR}"

if [[ $# -lt 1 ]]; then
  echo "mcp-custom-serve: missing backend command" >&2
  echo "usage: mcp-custom-serve.sh <command> [args...]" >&2
  exit 2
fi

BACKEND_CMD=("$@")
BACKEND_NAME="${MCP_CUSTOM_NAME:-$(basename "${BACKEND_CMD[0]}")}"
LOG_FILE="${MCP_CUSTOM_LOG_DIR}/${BACKEND_NAME}-$(date +%Y%m%d-%H%M%S)-$$.log"

_log() {
  local msg="[$(date -Iseconds)] [mcp-custom-serve/${BACKEND_NAME} pid=$$] $*"
  printf '%s\n' "${msg}" >>"${LOG_FILE}"
  printf '%s\n' "${msg}" >&2
}

_log "========== custom MCP backend starting =========="
_log "command: ${BACKEND_CMD[*]}"
_log "cwd: $(pwd)"
_log "log file: ${LOG_FILE}"
_log "MCP rule: write diagnostics to stderr only — stdout is JSON-RPC"

exec "${BACKEND_CMD[@]}"
