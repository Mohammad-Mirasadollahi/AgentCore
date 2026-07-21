# ai-toolstack-sync — orchestration (MCP wiring via install.sh).

sync_run_backend_graph_ensure() {
  return 0
}

sync_run_plan() {
  sync_section "ThinkingSOC ai-toolstack sync (plan)"
  sync_info "Repo: ${REPO_ROOT}"
  GIT_CHANGE_JSON="$(sync_git_change_stats)"
  export GIT_CHANGE_JSON
  sync_decide_plan

  sync_section "Plan"
  sync_print_plan_header "${GIT_CHANGE_JSON}"
  sync_print_plan_stages

  if [[ "${CHECK_ONLY}" == true ]]; then
    sync_info "Check only — no stages executed"
    exit 0
  fi

  if [[ "${QUIET}" == true ]]; then
    exit 0
  fi
}

sync_run_daemons() {
  return 0
}

sync_execute_stages() {
  sync_section "Summary"
  sync_info "Nothing to sync. Use ./ai-toolstack/install.sh for MCP wiring."
  exit 0
}

sync_main() {
  cd "${REPO_ROOT}" || { echo "FAIL: cannot cd ${REPO_ROOT}" >&2; exit 1; }
  mkdir -p "${AI_TOOLSTACK_LOCAL}" "${LOG_DIR}"
  sync_acquire_lock
  sync_install_err_trap
  sync_run_plan
  sync_execute_stages
}
