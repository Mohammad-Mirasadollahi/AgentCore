#!/usr/bin/env bash
# Diagnose mcp-lazy hangs: test each backend individually, then full init.
# Usage: ./ai-toolstack/scripts/mcp-lazy-diagnose.sh [--quick]
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${_SCRIPT_DIR}/../lib/paths.sh"
# shellcheck source=../lib/resolve-node.sh
source "${AI_TOOLSTACK_ROOT}/lib/resolve-node.sh"
# shellcheck source=../lib/mcp-lazy-debug.sh
source "${AI_TOOLSTACK_ROOT}/lib/mcp-lazy-debug.sh"

QUICK=0
if [[ "${1:-}" == "--quick" ]]; then
  QUICK=1
fi

RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
CYAN='\033[36m'
DIM='\033[2m'
RESET='\033[0m'

info() { printf '%b%s%b\n' "${CYAN}" "$*" "${RESET}"; }
pass() { printf '  %b✓%b %s\n' "${GREEN}" "${RESET}" "$*"; }
fail() { printf '  %b✗%b %s\n' "${RED}" "${RESET}" "$*"; }
warn() { printf '  %b!%b %s\n' "${YELLOW}" "${RESET}" "$*"; }

CONNECT_TIMEOUT="${MCP_LAZY_DIAG_CONNECT_TIMEOUT:-45}"

if ! ensure_node_toolchain; then
  fail "node/npx not found — run ./ai-toolstack/install.sh"
  exit 127
fi
export PATH="${NODE_TOOLCHAIN_BIN}:${PATH}"
export MCP_LAZY_VERBOSE=1
export MCP_LAZY_DEBUG=verbose
mcp_lazy_enable_node_preload

SERVERS_JSON="${HOME}/.mcp-lazy/servers.json"
DIAG_LOG="${MCP_LAZY_LOG_DIR}/diagnose-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "${MCP_LAZY_LOG_DIR}"

exec > >(tee -a "${DIAG_LOG}") 2>&1

info "mcp-lazy diagnose — log: ${DIAG_LOG}"
info "connect timeout per backend: ${CONNECT_TIMEOUT}s"
echo ""

if [[ ! -f "${SERVERS_JSON}" ]]; then
  fail "missing ${SERVERS_JSON} — run ./ai-toolstack/install.sh"
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  warn "jq not installed — per-server tests skipped"
  QUICK=1
fi

# --- Per-backend stdio handshake test (most useful for hang diagnosis) ---
test_backend() {
  local name="$1"
  local command args_json cwd env_json
  command="$(jq -r ".servers[\"${name}\"].command // empty" "${SERVERS_JSON}")"
  args_json="$(jq -c ".servers[\"${name}\"].args // []" "${SERVERS_JSON}")"
  cwd="$(jq -r ".servers[\"${name}\"].cwd // empty" "${SERVERS_JSON}")"
  env_json="$(jq -c ".servers[\"${name}\"].env // {}" "${SERVERS_JSON}")"

  if [[ -z "${command}" ]]; then
    fail "${name}: no command (URL-only server — skipped)"
    return 1
  fi

  info "Testing backend: ${name}"
  printf '    command: %s\n' "${command}"
  printf '    args:    %s\n' "${args_json}"
  [[ -n "${cwd}" ]] && printf '    cwd:     %s\n' "${cwd}"

  if [[ ! -x "${command}" && "${command}" != *"/"* ]]; then
    if ! command -v "${command}" >/dev/null 2>&1; then
      fail "${name}: command not found: ${command}"
      return 1
    fi
  elif [[ "${command}" == */* && ! -x "${command}" ]]; then
    fail "${name}: not executable: ${command}"
    return 1
  fi

  local server_cfg probe_out probe_rc probe_script
  probe_script="${AI_TOOLSTACK_SCRIPTS}/mcp-backend-probe.mjs"
  server_cfg="$(jq -c ".servers[\"${name}\"]" "${SERVERS_JSON}")"
  probe_out="$(
    MCP_LOCAL_NODE_MODULES="${AI_TOOLSTACK_LOCAL}/node_modules" \
    MCP_PROBE_TIMEOUT_MS=$((CONNECT_TIMEOUT * 1000)) MCP_LAZY_VERBOSE=1 \
    timeout "${CONNECT_TIMEOUT}" "${NODE_TOOLCHAIN_BIN}/node" "${probe_script}" "${server_cfg}" "${name}" 2>&1
  )" || probe_rc=$?
  probe_rc=${probe_rc:-0}

  if [[ ${probe_rc} -eq 0 ]]; then
    pass "${name}: ${probe_out}"
    return 0
  fi
  if [[ ${probe_rc} -eq 124 ]]; then
    fail "${name}: TIMEOUT after ${CONNECT_TIMEOUT}s — likely cause of Cursor hang"
  else
    fail "${name}: ${probe_out}"
  fi
  return 1
}

failed=0
if [[ ${QUICK} -eq 0 ]]; then
  info "Phase 1: per-backend MCP initialize probe"
  echo ""
  while IFS= read -r server; do
    test_backend "${server}" || failed=$((failed + 1))
    echo ""
  done < <(jq -r '.servers | keys[]' "${SERVERS_JSON}")
fi

info "Phase 2: mcp-lazy doctor"
echo ""
mcp_lazy_exec_args
if "${MCP_LAZY_CMD[@]}" doctor 2>&1; then
  pass "doctor completed"
else
  fail "doctor failed"
  failed=$((failed + 1))
fi
echo ""

info "Phase 3: mcp-lazy init (parallel discovery — same path as cache-miss serve)"
echo ""
init_start=$(date +%s)
if timeout 180 env MCP_LAZY_VERBOSE=1 MCP_LAZY_DEBUG=verbose MCP_LAZY_LOG_DIR="${MCP_LAZY_LOG_DIR}" \
  "${MCP_LAZY_CMD[@]}" init 2>&1; then
  init_elapsed=$(( $(date +%s) - init_start ))
  pass "init completed in ${init_elapsed}s"
else
  init_rc=$?
  init_elapsed=$(( $(date +%s) - init_start ))
  if [[ ${init_rc} -eq 124 ]]; then
    fail "init TIMED OUT after 180s — a backend is blocking parallel discovery"
  else
    fail "init failed (exit ${init_rc}) after ${init_elapsed}s"
  fi
  failed=$((failed + 1))
fi
echo ""

info "Phase 4: cache vs servers.json freshness"
cache="${HOME}/.mcp-lazy/tool-cache.json"
if [[ -f "${cache}" && -f "${SERVERS_JSON}" ]]; then
  if [[ "${cache}" -ot "${SERVERS_JSON}" ]]; then
    warn "tool-cache.json is OLDER than servers.json — next Cursor MCP start will re-discover (slow/hang risk)"
    warn "fix: npx mcp-lazy init  OR  Reload after ./ai-toolstack/install.sh"
  else
    pass "tool-cache.json is up to date"
  fi
fi
echo ""

info "Log files:"
printf '  %s\n' "${DIAG_LOG}"
printf '  %s\n' "${MCP_LAZY_LOG_DIR}"/session-*.log 2>/dev/null || true
printf '  %s\n' "${MCP_LAZY_LOG_DIR}"/spawn.log 2>/dev/null || true
echo ""

if [[ ${failed} -gt 0 ]]; then
  fail "${failed} check(s) failed — see log above"
  echo ""
  info "Common hang causes:"
  echo "  1. Backend uses nested npx (use local binary like memory server)"
  echo "  2. Backend never responds to MCP initialize (stdio deadlock)"
  echo "  3. tool-cache stale → serve runs parallel discovery on every Cursor start"
  echo "  4. Custom MCP writes debug output to stdout (breaks JSON-RPC)"
  exit 1
fi

pass "All checks passed"
exit 0
