# Stage 02: project virtualenv + editable agentcore CLI on PATH.
# shellcheck shell=bash

_venv_dir() {
  printf '%s\n' "${AGENTCORE_VENV_DIR:-.venv}"
}

_venv_path() {
  printf '%s/%s\n' "${AGENTCORE_ROOT}" "$(_venv_dir)"
}

# Virtualenv + imports only (PATH shim checked separately).
stage_02_venv_only_check() {
  local errors=0
  local venv_path py cli
  venv_path="$(_venv_path)"
  py="${venv_path}/bin/python"
  cli="${venv_path}/bin/agentcore"

  if [[ ! -x "${py}" ]]; then
    warn "missing ${py}"
    errors=1
  else
    ok "venv python: $(${py} --version 2>&1)"
  fi

  if [[ ! -x "${cli}" ]]; then
    warn "missing ${cli} (editable install incomplete)"
    errors=1
  else
    ok "venv agentcore present"
  fi

  if [[ -x "${py}" ]]; then
    if ! "${py}" -c 'import fastapi, httpx, pytest, psycopg, agentcore_cli, usage_profile'; then
      warn "required Python imports failed inside venv"
      errors=1
    else
      ok "core Python imports OK"
    fi
  fi

  return "${errors}"
}

stage_02_venv_check() {
  local errors=0
  stage_02_venv_only_check || errors=1

  if ! user_cli_on_path; then
    warn "missing ${HOME}/.local/bin/agentcore (PATH shim)"
    errors=1
  else
    ok "user PATH shim: ${HOME}/.local/bin/agentcore"
  fi

  return "${errors}"
}

stage_02_venv_run() {
  local venv_dir venv_path
  venv_dir="$(_venv_dir)"
  venv_path="$(_venv_path)"
  banner "Stage 02/05 — Python virtualenv (${venv_dir})"

  if [[ "${INSTALL_CHECK_ONLY}" == "1" ]]; then
    stage_02_venv_check || fail "venv check failed — run: bash install.sh (or bash scripts/ensure-venv.sh)"
    mark_stage "02_venv" "checked"
    return 0
  fi

  if ! stage_02_venv_only_check; then
    require_file "${AGENTCORE_ROOT}/scripts/ensure-venv.sh" "repo scripts missing"
    require_file "${AGENTCORE_ROOT}/pyproject.toml" "run install from AgentCore repo root"
    require_file "${AGENTCORE_ROOT}/requirements-dev.txt"

    local py
    py="$(python_bin)" || fail "Python 3.12+ required before creating venv"

    info "Creating/refreshing ${venv_dir} with ${py}…"
    if [[ "${py}" == "python3.12" ]] && [[ ! -x "${venv_path}/bin/python" ]]; then
      run "${py}" -m venv "${venv_path}"
    fi
    run env AGENTCORE_VENV_DIR="${venv_dir}" bash "${AGENTCORE_ROOT}/scripts/ensure-venv.sh"
    stage_02_venv_only_check || fail "venv verification failed after ensure-venv.sh"
  else
    ok "Virtualenv already ready"
  fi

  # Always (re)install PATH shim + shell rc — never skip when venv was already OK.
  install_cli_on_path "${venv_path}/bin/agentcore"
  stage_02_venv_check || fail "venv/PATH verification failed after path install"
  seed_repo_operator_files
  mark_stage "02_venv" "ok"
  ok "Stage 02 complete"
}
