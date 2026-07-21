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

INSTALL_STAGES=(
  "01_prerequisites:stage_01_prerequisites_run"
  "02_venv:stage_02_venv_run"
  "03_compose_env:stage_03_compose_env_run"
  "04_docker_infra:stage_04_docker_infra_run"
  "05_verify:stage_05_verify_run"
)

list_install_stages() {
  local entry name
  echo "AgentCore install stages (in order):"
  for entry in "${INSTALL_STAGES[@]}"; do
    name="${entry%%:*}"
    echo "  - ${name}"
  done
}

run_install_stage() {
  local want="$1"
  local entry name fn
  for entry in "${INSTALL_STAGES[@]}"; do
    name="${entry%%:*}"
    fn="${entry#*:}"
    if [[ "${name}" == "${want}" ]]; then
      "${fn}"
      return $?
    fi
  done
  fail "unknown stage: ${want} (use --list-stages)"
}

run_install_all() {
  local entry fn
  ensure_state_dir
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
      run_install_stage "01_prerequisites"
      ;;
    all|*)
      run_install_all
      ;;
  esac
}
