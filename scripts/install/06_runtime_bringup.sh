# Stage 06: bring AgentCore application runtime up (host MCP or Docker mcp-gateway).
# shellcheck shell=bash

_compose_app() {
  docker compose --env-file "${COMPOSE_ENV_FILE}" -f "${COMPOSE_FILE}" "$@"
}

_venv_cli() {
  printf '%s/%s/bin/agentcore\n' "${AGENTCORE_ROOT}" "${AGENTCORE_VENV_DIR:-.venv}"
}

stage_06_runtime_bringup_check() {
  local errors=0
  local runtime="${INSTALL_RUNTIME:-venv}"

  if ! user_cli_on_path; then
    warn "agentcore not on user PATH (${HOME}/.local/bin/agentcore)"
    errors=1
  else
    ok "user PATH shim present"
  fi

  case "${runtime}" in
    venv|host)
      if [[ "${INSTALL_SKIP_INFRA}" == "1" || "${INSTALL_ROLE:-}" == "client" ]]; then
        ok "venv/client: infra skipped; CLI/PATH only — next: agentcore connect"
        return "${errors}"
      fi
      if ! stage_04_docker_infra_check; then
        warn "venv runtime needs healthy postgres/neo4j"
        errors=1
      fi
      ;;
    docker)
      local status
      status="$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
        agentcore-mcp-gateway-1 2>/dev/null || echo missing)"
      if [[ "${status}" != "healthy" ]]; then
        warn "mcp-gateway status=${status} (want healthy)"
        errors=1
      else
        ok "mcp-gateway healthy"
      fi
      ;;
    *)
      warn "unknown INSTALL_RUNTIME=${runtime}"
      errors=1
      ;;
  esac

  return "${errors}"
}

_stage_06_bringup_host() {
  local cli
  cli="$(_venv_cli)"
  # Prefer host MCP: stop container listener if present so :32500 is free.
  # Both profiles required — mcp-gateway depends_on postgres/neo4j (core).
  info "Stopping mcp-gateway container if running (host MCP will own the port)…"
  _compose_app --profile core --profile app stop mcp-gateway >/dev/null 2>&1 || true
  info "Starting host runtime (Compose core + MCP HTTP via agentcore service start)…"
  run "${cli}" service start
}

_stage_06_bringup_docker() {
  local wheelhouse_script
  wheelhouse_script="${AGENTCORE_ROOT}/scripts/build-wheelhouse.sh"
  require_file "${wheelhouse_script}"
  require_file "${AGENTCORE_ROOT}/backend/deployments/docker/Dockerfile.mcp-gateway"

  # Free MCP host port without tearing down Postgres/Neo4j.
  info "Stopping host MCP HTTP if running (frees MCP port for container)…"
  AGENTCORE_ROOT="${AGENTCORE_ROOT}" \
    "${AGENTCORE_ROOT}/${AGENTCORE_VENV_DIR:-.venv}/bin/python" - <<'PY' || true
import os
from pathlib import Path
from agentcore_cli.service_runtime.mcp import stop_mcp_http
stop_mcp_http(Path(os.environ["AGENTCORE_ROOT"]))
PY

  if [[ ! -d "${AGENTCORE_WHEELHOUSE}" ]] || ! find "${AGENTCORE_WHEELHOUSE}" -maxdepth 1 -name '*.whl' 2>/dev/null | grep -q .; then
    info "Building wheelhouse at ${AGENTCORE_WHEELHOUSE}…"
    run env AGENTCORE_WHEELHOUSE="${AGENTCORE_WHEELHOUSE}" bash "${wheelhouse_script}"
  else
    ok "Wheelhouse present: ${AGENTCORE_WHEELHOUSE}"
  fi

  info "Starting Compose profiles core+app (postgres, neo4j, mcp-gateway)…"
  AGENTCORE_WHEELHOUSE="${AGENTCORE_WHEELHOUSE}" _compose_app \
    --profile core --profile app up -d --build postgres neo4j mcp-gateway

  local i status
  status="missing"
  for i in $(seq 1 60); do
    status="$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
      agentcore-mcp-gateway-1 2>/dev/null || echo missing)"
    if [[ "${status}" == "healthy" ]]; then
      break
    fi
    if [[ "${status}" == "exited" || "${status}" == "dead" ]]; then
      docker logs agentcore-mcp-gateway-1 2>&1 | tail -80 || true
      fail "mcp-gateway container ${status}"
    fi
    sleep 2
  done
  [[ "${status}" == "healthy" ]] || fail "mcp-gateway not healthy (status=${status})"
  ok "mcp-gateway healthy on port ${AGENTCORE_MCP_HTTP_PORT:-32500}"
}

stage_06_runtime_bringup_run() {
  local runtime="${INSTALL_RUNTIME:-venv}"
  local role="${INSTALL_ROLE:-server}"
  banner "Stage 06/06 — Bring up runtime (${runtime}, role=${role})"

  # PATH in every mode (including check / skip-infra).
  if [[ "${INSTALL_CHECK_ONLY}" != "1" ]]; then
    ensure_agentcore_on_path
  fi

  if [[ "${INSTALL_CHECK_ONLY}" == "1" ]]; then
    stage_06_runtime_bringup_check || fail "runtime bring-up check failed"
    mark_stage "06_runtime_bringup" "checked"
    return 0
  fi

  if [[ "${INSTALL_SKIP_INFRA}" == "1" || "${role}" == "client" ]]; then
    info "Skipping application bring-up (client / --skip-infra); PATH still installed"
    mark_stage "06_runtime_bringup" "skipped"
    echo >&2
    banner "Client install finished"
    cat >&2 <<EOF
Next steps:
  1. Open a new shell if needed so agentcore is on PATH (~/.local/bin)
  2. From your app repo:  agentcore connect
     (interactive SSH wizard, or agentcore connect edit to re-auth)
  3. Docs: docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md
EOF
    return 0
  fi

  case "${runtime}" in
    venv|host) _stage_06_bringup_host ;;
    docker) _stage_06_bringup_docker ;;
    *) fail "unknown INSTALL_RUNTIME=${runtime}" ;;
  esac

  stage_06_runtime_bringup_check || fail "runtime bring-up verification failed"
  mark_stage "06_runtime_bringup" "ok"
  ok "Stage 06 complete (runtime=${runtime})"
  stamp_agentcore_install_root_markers || warn "install-root marker stamp failed (non-fatal)"

  echo >&2
  if [[ "${role}" == "both" ]]; then
    banner "AgentCore BOTH (dogfood) install finished"
    cat >&2 <<EOF
Next steps:
  1. agentcore is on PATH via ~/.local/bin (open a new shell if \`command -v agentcore\` fails)
  2. Local stack + MCP mode: ${runtime} — run: agentcore sync
  3. Same-host IDE connect: agentcore connect   (local-stdio; no remote server required)
  4. Run:  agentcore --help && agentcore doctor
  5. MCP health: curl -sS http://127.0.0.1:${AGENTCORE_MCP_HTTP_PORT:-32500}/health
  6. Docs:  docs/08-software-engineering-architecture/39-local-install-runbook.md

Compose env (secrets): ${COMPOSE_ENV_FILE}
Re-check anytime:       bash install.sh --check --non-interactive --role both --runtime ${runtime}
EOF
  else
    banner "AgentCore SERVER install finished"
    cat >&2 <<EOF
Next steps:
  1. agentcore is on the SERVER PATH via ~/.local/bin (open a new shell if \`command -v agentcore\` fails)
  2. Server MCP mode: ${runtime}
  3. On coding-agent machines: bash install.sh --role client   then   agentcore connect
     Same-host dogfood instead: bash install.sh --role both
  4. Run:  agentcore --help && agentcore doctor
  5. MCP health: curl -sS http://127.0.0.1:${AGENTCORE_MCP_HTTP_PORT:-32500}/health
  6. Docs:  docs/08-software-engineering-architecture/39-local-install-runbook.md
            docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md

Compose env (secrets): ${COMPOSE_ENV_FILE}
Re-check anytime:       bash install.sh --check --non-interactive --role server --runtime ${runtime}
EOF
  fi
}
