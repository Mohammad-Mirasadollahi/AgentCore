# ai-toolstack-sync — quiet-aware log helpers.

sync_section() { [[ "${QUIET}" == true ]] || ts_section "$*"; }
sync_info() { [[ "${QUIET}" == true ]] || ts_log "[ai-toolstack-sync] $*"; }
sync_warn() { ts_log "[ai-toolstack-sync] WARN: $*" >&2; }
sync_skip() { [[ "${QUIET}" == true ]] || ts_log "  SKIP  $*"; }
sync_plan() { ts_log "  PLAN  $*"; }

# Stage diagnostics (always logged — needed when --quiet hides normal progress).
sync_diag() { ts_log "[ai-toolstack-sync] DIAG: $*" >&2; }

sync_stage_begin() {
  SYNC_CURRENT_STAGE="${1}"
  SYNC_STAGE_START=${SECONDS}
  sync_diag "stage begin: ${1}"
}

sync_stage_done() {
  local stage="${1}"
  local exit_code="${2:-0}"
  local elapsed=$(( SECONDS - ${SYNC_STAGE_START:-SECONDS} ))
  if [[ "${exit_code}" -eq 0 ]]; then
    sync_diag "stage complete: ${stage} (${elapsed}s wall)"
  else
    sync_warn "stage failed: ${stage} (exit ${exit_code}, ${elapsed}s wall)"
  fi
}

# Log when set -e aborts before the next pipeline stage (e.g. helper function exit 1).
sync_on_err() {
  local exit_code="${1:-$?}"
  trap - ERR
  sync_warn "Sync aborted during stage: ${SYNC_CURRENT_STAGE:-unknown} (exit ${exit_code})"
  sync_warn "Failed command: ${BASH_COMMAND}"
  if [[ ${#BASH_SOURCE[@]} -gt 1 ]]; then
    sync_warn "At: ${BASH_SOURCE[1]}:${BASH_LINENO[0]}"
  fi
  sync_warn "set -e stopped the pipeline before the next stage could run."
  sync_warn "Typical cause: a function's last command returned non-zero (e.g. [[ cond ]] && cmd when cond is false)."
  sync_warn "Re-run with: bash -x ./ai-toolstack/scripts/ai-toolstack.sh <flags>"
  exit "${exit_code}"
}

sync_install_err_trap() {
  [[ "${SYNC_ERR_TRAP_INSTALLED}" == true ]] && return 0
  SYNC_ERR_TRAP_INSTALLED=true
  trap 'sync_on_err $?' ERR
}
