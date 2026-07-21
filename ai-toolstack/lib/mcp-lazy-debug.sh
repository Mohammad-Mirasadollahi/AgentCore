#!/usr/bin/env bash
# Shared verbose logging helpers for mcp-lazy (Cursor MCP entry + diagnostics).
# shellcheck disable=SC2034
set -euo pipefail

_mcp_lazy_debug_lib="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "${_mcp_lazy_debug_lib}/paths.sh"

export MCP_LAZY_LOG_DIR="${MCP_LAZY_LOG_DIR:-${AI_TOOLSTACK_DATA}/mcp-lazy/logs}"
export MCP_LAZY_VERBOSE="${MCP_LAZY_VERBOSE:-0}"
export MCP_LAZY_DEBUG="${MCP_LAZY_DEBUG:-0}"

mkdir -p "${MCP_LAZY_LOG_DIR}"

# One log file per wrapper invocation (Cursor may restart MCP often).
if [[ -z "${MCP_LAZY_SESSION_LOG:-}" ]]; then
  export MCP_LAZY_SESSION_LOG="${MCP_LAZY_LOG_DIR}/session-$(date +%Y%m%d-%H%M%S)-$$.log"
fi

mcp_lazy_log() {
  local msg="[$(date -Iseconds)] [mcp-lazy-serve pid=$$ ppid=${PPID:-?}] $*"
  printf '%s\n' "${msg}" >>"${MCP_LAZY_SESSION_LOG}"
  printf '%s\n' "${msg}" >&2
}

mcp_lazy_log_env() {
  mcp_lazy_log "MCP_LAZY_VERBOSE=${MCP_LAZY_VERBOSE}"
  mcp_lazy_log "MCP_LAZY_LOG_DIR=${MCP_LAZY_LOG_DIR}"
  mcp_lazy_log "MCP_LAZY_SESSION_LOG=${MCP_LAZY_SESSION_LOG}"
  mcp_lazy_log "AI_TOOLSTACK_ROOT=${AI_TOOLSTACK_ROOT}"
  mcp_lazy_log "NODE_TOOLCHAIN_BIN=${NODE_TOOLCHAIN_BIN:-unset}"
  mcp_lazy_log "PATH(head)=${PATH%%:*}"
}

mcp_lazy_log_servers_json() {
  local servers_json="${HOME}/.mcp-lazy/servers.json"
  if [[ ! -e "${servers_json}" ]]; then
    mcp_lazy_log "servers.json: MISSING at ${servers_json}"
    return 1
  fi
  mcp_lazy_log "servers.json: $(readlink -f "${servers_json}" 2>/dev/null || echo "${servers_json}")"
  if command -v jq >/dev/null 2>&1; then
    mcp_lazy_log "registered servers: $(jq -r '.servers | keys | join(", ")' "${servers_json}" 2>/dev/null || echo PARSE_ERROR)"
    jq -r '.servers | to_entries[] | "  server \(.key): cmd=\(.value.command // "none") args=\(.value.args // [] | join(" "))"' \
      "${servers_json}" 2>/dev/null | while read -r line; do mcp_lazy_log "${line}"; done
  else
    mcp_lazy_log "servers.json raw (no jq): $(tr -d '\n' <"${servers_json}" | head -c 500)"
  fi
}

mcp_lazy_log_tool_cache() {
  local cache="${HOME}/.mcp-lazy/tool-cache.json"
  if [[ ! -f "${cache}" ]]; then
    mcp_lazy_log "tool-cache.json: MISSING (serve will run discovery — can hang 30s+ per backend)"
    return 0
  fi
  local mtime size
  mtime="$(stat -c '%y' "${cache}" 2>/dev/null || stat -f '%Sm' "${cache}" 2>/dev/null || echo unknown)"
  size="$(wc -c <"${cache}" | tr -d ' ')"
  mcp_lazy_log "tool-cache.json: ${size} bytes mtime=${mtime}"
  if command -v jq >/dev/null 2>&1; then
    mcp_lazy_log "cached tools: $(jq -r '.tools | length' "${cache}" 2>/dev/null || echo ?)"
  fi
}

mcp_lazy_enable_node_preload() {
  local preload="${AI_TOOLSTACK_ROOT}/lib/mcp-lazy-debug-preload.cjs"
  if [[ ! -f "${preload}" ]]; then
    mcp_lazy_log "WARN: debug preload missing: ${preload}"
    return 0
  fi
  local req="--require=${preload}"
  if [[ "${NODE_OPTIONS:-}" == *"${preload}"* ]]; then
    mcp_lazy_log "NODE_OPTIONS already has debug preload"
    return 0
  fi
  if [[ -n "${NODE_OPTIONS:-}" ]]; then
    export NODE_OPTIONS="${req} ${NODE_OPTIONS}"
  else
    export NODE_OPTIONS="${req}"
  fi
  mcp_lazy_log "NODE_OPTIONS=${NODE_OPTIONS}"
}

resolve_mcp_lazy_bin() {
  local local_bin="${AI_TOOLSTACK_LOCAL}/node_modules/.bin/mcp-lazy"
  if [[ -x "${local_bin}" ]]; then
    echo "${local_bin}"
    return 0
  fi
  if [[ -n "${NODE_TOOLCHAIN_BIN:-}" && -x "${NODE_TOOLCHAIN_BIN}/npx" ]]; then
    echo "${NODE_TOOLCHAIN_BIN}/npx"
    return 0
  fi
  command -v npx 2>/dev/null || echo "npx"
}

mcp_lazy_exec_args() {
  local bin
  bin="$(resolve_mcp_lazy_bin)"
  if [[ "${bin}" == *"/npx" || "${bin}" == "npx" ]]; then
    mcp_lazy_log "using npx -y mcp-lazy (consider ./ai-toolstack/install.sh for local binary)"
    MCP_LAZY_CMD=("${bin}" "-y" "mcp-lazy")
  else
    mcp_lazy_log "using local mcp-lazy binary: ${bin}"
    MCP_LAZY_CMD=("${bin}")
  fi
}
