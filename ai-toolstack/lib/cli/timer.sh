#!/usr/bin/env bash
# Cron timer for ai-toolstack sync — internal; use: ai-toolstack.sh timer install
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../paths.sh
source "${_SCRIPT_DIR}/../paths.sh"

CLI_SH="${AI_TOOLSTACK_SCRIPTS}/ai-toolstack.sh"
MARKER="# ai-toolstack-sync-timer (ThinkingSOC)"
CRON_LINE="*/55 * * * * cd ${REPO_ROOT} && ${CLI_SH} --background --quiet >> ${HOME}/.cache/ai-toolstack-sync-cron.log 2>&1 ${MARKER}"

fail() { echo "FAIL: $*" >&2; exit 1; }
info() { echo "[ai-toolstack timer] $*"; }

install_timer() {
  [[ -x "${CLI_SH}" ]] || fail "missing ${CLI_SH}"
  local tmp existing
  tmp="$(mktemp)"
  existing="$(crontab -l 2>/dev/null || true)"
  if echo "${existing}" | grep -Fq "${MARKER}"; then
    info "Already installed"
    status_timer
    return 0
  fi
  { echo "${existing}"; echo "${CRON_LINE}"; } | sed '/^$/d' > "${tmp}"
  crontab "${tmp}"
  rm -f "${tmp}"
  info "Installed: every 5 minutes"
}

uninstall_timer() {
  if ! crontab -l 2>/dev/null | grep -Fq "${MARKER}"; then
    info "Not installed"
    return 0
  fi
  crontab -l 2>/dev/null | grep -Fv "${MARKER}" | sed '/^$/d' | crontab -
  info "Removed cron entry"
}

status_timer() {
  if crontab -l 2>/dev/null | grep -Fq "${MARKER}"; then
    info "Cron: enabled (every 5 min)"
    crontab -l 2>/dev/null | grep -F "${MARKER}" | sed 's/^/  /'
  else
    info "Cron: not installed"
  fi
}

case "${1:-install}" in
  install) install_timer ;;
  status) status_timer ;;
  uninstall|remove) uninstall_timer ;;
  *) fail "usage: ai-toolstack.sh timer install|status|uninstall" ;;
esac
