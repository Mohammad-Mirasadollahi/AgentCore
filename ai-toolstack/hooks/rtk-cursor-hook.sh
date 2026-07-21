#!/usr/bin/env bash
# Cursor preToolUse hook: RTK Shell lane + thinkingSOC watermark for Headroom bypass.
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${_SCRIPT_DIR}/../lib/paths.sh"

MARKER='<!-- thinkingSOC:rtk-lane -->'

# All rtk subprocesses (including `hook cursor`) need a writable XDG path in Cursor sandbox.
ensure_rtk_xdg() {
  mkdir -p "${RTK_XDG_DATA_HOME}/rtk" 2>/dev/null || true
  export XDG_DATA_HOME="${RTK_XDG_DATA_HOME}"
}

resolve_rtk_bin() {
  for c in "${RTK_BIN:-}" "${HOME}/.local/bin/rtk" "/usr/local/bin/rtk"; do
    [[ -n "${c}" && -x "${c}" ]] && echo "${c}" && return 0
  done
  command -v rtk 2>/dev/null || true
}

RTK_BIN_RESOLVED="$(resolve_rtk_bin)"
if [[ -z "${RTK_BIN_RESOLVED}" || ! -x "${RTK_BIN_RESOLVED}" ]]; then
  printf '{}\n'
  exit 0
fi

ensure_rtk_xdg

if ! command -v jq >/dev/null 2>&1; then
  exec env XDG_DATA_HOME="${RTK_XDG_DATA_HOME}" "${RTK_BIN_RESOLVED}" hook cursor
fi

INPUT="$(cat)"
TOOL="$(printf '%s' "${INPUT}" | jq -r '.tool_name // empty')"
if [[ "${TOOL}" != "Shell" ]]; then
  printf '%s' "${INPUT}" | env XDG_DATA_HOME="${RTK_XDG_DATA_HOME}" "${RTK_BIN_RESOLVED}" hook cursor 2>/dev/null || printf '{}\n'
  exit 0
fi

CMD="$(printf '%s' "${INPUT}" | jq -r '.tool_input.command // empty')"
if [[ -z "${CMD}" ]]; then
  printf '%s' "${INPUT}" | env XDG_DATA_HOME="${RTK_XDG_DATA_HOME}" "${RTK_BIN_RESOLVED}" hook cursor 2>/dev/null || printf '{}\n'
  exit 0
fi

# Internal tooling (tests, install, MCP serve) — not SOC diagnostic shell output.
should_skip_rtk_wrap() {
  case "${CMD}" in
    node\ ai-toolstack/*|python3\ ai-toolstack/*|./ai-toolstack/*|./*ai-toolstack/*)
      return 0 ;;
    *compression-lanes-*|*headroom-mcp-serve*|*headroom_mcp_guard*)
      return 0 ;;
    /usr/local/bin/node\ *ai-toolstack/*|/root/.nvm/*/bin/node\ *ai-toolstack/*)
      return 0 ;;
  esac
  # Absolute repo paths (agent may use full paths)
  if [[ "${CMD}" == *"/ai-toolstack/scripts/"* && "${CMD}" == *node* ]]; then
    return 0
  fi
  return 1
}

if should_skip_rtk_wrap; then
  RTK_OUT="$(printf '%s' "${INPUT}" | env XDG_DATA_HOME="${RTK_XDG_DATA_HOME}" "${RTK_BIN_RESOLVED}" hook cursor 2>/dev/null || echo '{}')"
  printf '%s' "${RTK_OUT}" | jq --arg cmd "${CMD}" '
    .permission //= "allow" |
    .updated_input //= {} |
    .updated_input.command = $cmd
  '
  exit 0
fi

# RTK filters command output; append lane marker for Headroom hard bypass.
# XDG_DATA_HOME → workspace path so sandboxed Shell can write history.db (no warn line).
_rtk_wrap_body() {
  local inner="$1"
  printf "mkdir -p '%s/rtk' 2>/dev/null; XDG_DATA_HOME='%s' %s" \
    "${RTK_XDG_DATA_HOME}" "${RTK_XDG_DATA_HOME}" "${inner}"
}
if [[ "${CMD}" == rtk\ * ]]; then
  WRAPPED="$(_rtk_wrap_body "${CMD}"); printf '%s\\n' '${MARKER}'"
else
  WRAPPED="$(_rtk_wrap_body "rtk ${CMD}"); printf '%s\\n' '${MARKER}'"
fi

RTK_OUT="$(printf '%s' "${INPUT}" | env XDG_DATA_HOME="${RTK_XDG_DATA_HOME}" "${RTK_BIN_RESOLVED}" hook cursor 2>/dev/null || echo '{}')"
printf '%s' "${RTK_OUT}" | jq --arg cmd "${WRAPPED}" '
  .permission //= "allow" |
  .updated_input //= {} |
  .updated_input.command = $cmd
'
