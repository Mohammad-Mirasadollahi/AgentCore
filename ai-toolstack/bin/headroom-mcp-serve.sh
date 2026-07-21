#!/usr/bin/env bash
# Headroom MCP entry for mcp-lazy — compress / retrieve / stats (stdio).
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${_SCRIPT_DIR}/../lib/paths.sh"
# shellcheck source=../config/headroom-env.sh
source "${HEADROOM_ENV_SH}"

mkdir -p "${HEADROOM_DIR}" "${HEADROOM_DIR}/logs"

resolve_headroom_bin() {
  for c in "${HEADROOM_BIN:-}" "${HOME}/.local/bin/headroom" "${HOME}/.local/share/pipx/venvs/headroom-ai/bin/headroom"; do
    [[ -n "${c}" && -x "${c}" ]] && echo "${c}" && return 0
  done
  command -v headroom 2>/dev/null || echo "headroom"
}

HEADROOM_BIN="$(resolve_headroom_bin)"
HEADROOM_BIN_REAL="$(readlink -f "${HEADROOM_BIN}" 2>/dev/null || echo "${HEADROOM_BIN}")"
HEADROOM_VENV_BIN="$(dirname "${HEADROOM_BIN_REAL}")"
HEADROOM_PYTHON="${HEADROOM_VENV_BIN}/python3"
if [[ ! -x "${HEADROOM_PYTHON}" ]]; then
  HEADROOM_PYTHON="$(command -v python3 2>/dev/null || echo python3)"
fi
LOG_FILE="${HEADROOM_DIR}/logs/mcp-serve-$(date +%Y%m%d-%H%M%S)-$$.log"

_log() {
  local msg="[$(date -Iseconds)] [headroom-mcp-serve pid=$$] $*"
  printf '%s\n' "${msg}" >>"${LOG_FILE}"
  printf '%s\n' "${msg}" >&2
}

if [[ ! -x "${HEADROOM_BIN}" ]]; then
  _log "headroom binary not found at ${HEADROOM_BIN} — run: pipx install 'headroom-ai[mcp]' && ./ai-toolstack/install.sh"
  exit 127
fi

_log "========== Headroom MCP server starting =========="
_log "HEADROOM_BIN=${HEADROOM_BIN}"
_log "HEADROOM_WORKSPACE_DIR=${HEADROOM_WORKSPACE_DIR}"
_log "REPO_ROOT=${REPO_ROOT}"
_log "log file: ${LOG_FILE}"
_log "MCP rule: diagnostics on stderr only — stdout is JSON-RPC"
_log "tools: headroom_compress (RTK bypass guard), headroom_retrieve, headroom_stats, headroom_read"

GUARD_PY="${AI_TOOLSTACK_ROOT}/lib/headroom_mcp_guard.py"
if [[ -f "${GUARD_PY}" ]]; then
  _log "HEADROOM_PYTHON=${HEADROOM_PYTHON} (guard=${GUARD_PY})"
  exec "${HEADROOM_PYTHON}" "${GUARD_PY}"
fi

exec "${HEADROOM_BIN}" mcp serve "$@"
