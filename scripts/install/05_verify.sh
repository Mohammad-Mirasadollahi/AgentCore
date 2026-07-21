# Stage 05: end-to-end verification (doctor + optional ai-toolstack).
# shellcheck shell=bash

_venv_cli() {
  printf '%s/%s/bin/agentcore\n' "${AGENTCORE_ROOT}" "${AGENTCORE_VENV_DIR:-.venv}"
}

stage_05_verify_check() {
  local errors=0
  local cli
  cli="$(_venv_cli)"

  if [[ ! -x "${cli}" ]]; then
    warn "agentcore CLI missing at ${cli}"
    return 1
  fi

  if ! "${cli}" doctor >/dev/null; then
    warn "agentcore doctor failed"
    "${cli}" doctor || true
    errors=1
  else
    ok "agentcore doctor passed"
  fi

  if [[ "${INSTALL_SKIP_INFRA}" != "1" ]]; then
    if ! stage_04_docker_infra_check; then
      warn "infra not healthy during verify"
      errors=1
    fi
  fi

  return "${errors}"
}

stage_05_verify_run() {
  banner "Stage 05/05 — Verify installation"

  if [[ "${INSTALL_CHECK_ONLY}" == "1" ]]; then
    stage_01_prerequisites_check || fail "prerequisites failed"
    stage_02_venv_check || fail "venv failed"
    if [[ "${INSTALL_SKIP_INFRA}" != "1" ]]; then
      stage_03_compose_env_check || fail "compose env failed"
      stage_04_docker_infra_check || fail "infra failed"
    fi
    stage_05_verify_check || fail "verify failed"
    mark_stage "05_verify" "checked"
    ok "Check-only mode: all selected checks passed"
    return 0
  fi

  stage_05_verify_check || fail "verification failed — earlier stages incomplete"
  mark_stage "05_verify" "ok"

  if [[ "${INSTALL_WITH_AI_TOOLSTACK}" == "1" ]]; then
    banner "Optional — ai-toolstack (Cursor rules/skills)"
    local toolstack="${AGENTCORE_ROOT}/ai-toolstack/scripts/install-agentcore.sh"
    require_file "${toolstack}" "ai-toolstack missing from this checkout"
    run bash "${toolstack}"
    ok "ai-toolstack install finished (Reload Cursor window if open)"
  fi

  ok "Stage 05 complete"
  echo
  banner "AgentCore install finished"
  cat <<EOF
Next steps:
  1. Ensure ~/.local/bin is on PATH (open a new shell if needed)
  2. Run:  agentcore --help
  3. Run:  agentcore doctor
  4. Ports: agentcore ports show
  5. Docs:  docs/08-software-engineering-architecture/39-local-install-runbook.md

Compose env (secrets): ${COMPOSE_ENV_FILE}
Re-check anytime:       bash install.sh --check
EOF
}
