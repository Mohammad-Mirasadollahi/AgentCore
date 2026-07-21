# Stage 02: project virtualenv + editable agentcore CLI on PATH.
# shellcheck shell=bash

_venv_dir() {
  printf '%s\n' "${AGENTCORE_VENV_DIR:-.venv}"
}

_venv_path() {
  printf '%s/%s\n' "${AGENTCORE_ROOT}" "$(_venv_dir)"
}

stage_02_venv_check() {
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

  if stage_02_venv_check; then
    ok "Virtualenv already ready"
    if [[ -x "${venv_path}/bin/agentcore" ]]; then
      "${venv_path}/bin/agentcore" path install >/dev/null 2>&1 || true
    fi
    mark_stage "02_venv" "ok"
    return 0
  fi

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

  stage_02_venv_check || fail "venv verification failed after ensure-venv.sh"
  mark_stage "02_venv" "ok"
  ok "Stage 02 complete"
}
