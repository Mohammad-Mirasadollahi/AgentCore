# Load AgentCore install modules and run selected stages.
# shellcheck shell=bash

: "${AGENTCORE_ROOT:?AGENTCORE_ROOT must be set}"
: "${AGENTCORE_INSTALL_LIB:?AGENTCORE_INSTALL_LIB must be set}"

# shellcheck source=common.sh
source "${AGENTCORE_INSTALL_LIB}/common.sh"
# shellcheck source=01_prerequisites.sh
source "${AGENTCORE_INSTALL_LIB}/01_prerequisites.sh"
# shellcheck source=02_venv.sh
source "${AGENTCORE_INSTALL_LIB}/02_venv.sh"
# shellcheck source=03_compose_env.sh
source "${AGENTCORE_INSTALL_LIB}/03_compose_env.sh"
# shellcheck source=04_docker_infra.sh
source "${AGENTCORE_INSTALL_LIB}/04_docker_infra.sh"
# shellcheck source=05_verify.sh
source "${AGENTCORE_INSTALL_LIB}/05_verify.sh"
# shellcheck source=06_runtime_bringup.sh
source "${AGENTCORE_INSTALL_LIB}/06_runtime_bringup.sh"

INSTALL_STAGES=(
  "01_prerequisites:stage_01_prerequisites_run"
  "02_venv:stage_02_venv_run"
  "03_compose_env:stage_03_compose_env_run"
  "04_docker_infra:stage_04_docker_infra_run"
  "05_verify:stage_05_verify_run"
  "06_runtime_bringup:stage_06_runtime_bringup_run"
)

list_install_stages() {
  local entry name
  echo "AgentCore install stages (in order):"
  for entry in "${INSTALL_STAGES[@]}"; do
    name="${entry%%:*}"
    echo "  - ${name}"
  done
  echo "Runtime modes (SERVER only): host | docker — clients are never Dockerized"
}

run_install_stage() {
  local want="$1"
  local entry name fn
  for entry in "${INSTALL_STAGES[@]}"; do
    name="${entry%%:*}"
    fn="${entry#*:}"
    if [[ "${name}" == "${want}" ]]; then
      if [[ "${name}" == "06_runtime_bringup" ]]; then
        resolve_install_runtime
      fi
      "${fn}"
      return $?
    fi
  done
  fail "unknown stage: ${want} (use --list-stages)"
}

run_install_all() {
  local entry fn
  ensure_state_dir

  # Interactive / flagged choice before stages that depend on it.
  resolve_install_runtime

  # Human full installs must install OS prerequisites (ignore accidental skip).
  if [[ "${INSTALL_NONINTERACTIVE}" != "1" && "${INSTALL_SKIP_PREREQS}" == "1" ]]; then
    warn "Ignoring --skip-prerequisites for interactive install (prerequisites are required)"
    INSTALL_SKIP_PREREQS=0
    export INSTALL_SKIP_PREREQS
  fi

  for entry in "${INSTALL_STAGES[@]}"; do
    fn="${entry#*:}"
    "${fn}"
  done
}

install_main() {
  local mode="${1:-all}"
  local stage_name="${2:-}"

  case "${mode}" in
    list)
      list_install_stages
      ;;
    stage)
      [[ -n "${stage_name}" ]] || fail "--stage requires a stage name"
      run_install_stage "${stage_name}"
      ;;
    prerequisites-only)
      # Always install/check OS deps; no runtime prompt.
      INSTALL_SKIP_PREREQS=0
      export INSTALL_SKIP_PREREQS
      run_install_stage "01_prerequisites"
      ;;
    all|*)
      run_install_all
      ;;
  esac
}
