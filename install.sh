#!/usr/bin/env bash
# AgentCore one-command modular installer (beginner-safe, resumable, checkable).
#
# Usage:
#   bash install.sh
#   bash install.sh --runtime host
#   bash install.sh --runtime docker
#   bash install.sh --non-interactive --runtime host
#   bash install.sh --check
#   bash install.sh --prerequisites-only
#   bash install.sh --skip-infra
#   bash install.sh --with-frontend
#   bash install.sh --with-ai-toolstack
#   bash install.sh --stage 02_venv
#   bash install.sh --list-stages
#
# Docs:
#   docs/08-software-engineering-architecture/39-local-install-runbook.md
#   docs/08-software-engineering-architecture/43-app-docker-and-wheelhouse-runbook.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB="${ROOT}/scripts/install"

if [[ ! -f "${LIB}/load.sh" ]]; then
  echo "install.sh: missing ${LIB}/load.sh — incomplete checkout?" >&2
  exit 1
fi

export AGENTCORE_ROOT="${ROOT}"
export AGENTCORE_INSTALL_LIB="${LIB}"
export PATH="${HOME}/.local/bin:${PATH}"

MODE="all"
STAGE_NAME=""

usage() {
  cat <<'EOF'
AgentCore installer — modular local-dev bootstrap

Usage:
  bash install.sh [options]

Options:
  --runtime MODE          Bring-up mode: host | docker (skip interactive prompt)
  --non-interactive       No prompts; default --runtime host if omitted
  --check                 Verify stages only (no installs / no compose changes)
  --prerequisites-only    Install/check OS deps (Python, Docker, curl, git) then exit
  --skip-prerequisites    Do not apt-install (non-interactive/CI only; ignored interactively)
  --skip-infra            Skip Compose env + containers + runtime bring-up
  --with-frontend         Also ensure Node.js 18+ (for frontend/)
  --with-ai-toolstack     After verify, run ai-toolstack/scripts/install-agentcore.sh
  --stage NAME            Run a single stage (see --list-stages)
  --list-stages           Print stage names and exit
  --compose-timeout SEC   Health wait timeout (default 180)
  -h, --help              Show this help

Runtime modes:
  host    Compose Postgres/Neo4j + MCP HTTP from host .venv (agentcore service start)
  docker  Compose Postgres/Neo4j + MCP HTTP container (mcp-gateway from /opt wheelhouse)

Both modes always: install prerequisites (interactive), create .venv, put agentcore on PATH.

Default flow (all stages):
  01_prerequisites → 02_venv → 03_compose_env → 04_docker_infra → 05_verify → 06_runtime_bringup

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --runtime)
      [[ $# -ge 2 ]] || { echo "error: --runtime needs host|docker" >&2; exit 64; }
      export INSTALL_RUNTIME="$2"
      shift 2
      ;;
    --check)
      export INSTALL_CHECK_ONLY=1
      shift
      ;;
    --prerequisites-only)
      MODE="prerequisites-only"
      shift
      ;;
    --skip-prerequisites)
      export INSTALL_SKIP_PREREQS=1
      shift
      ;;
    --skip-infra)
      export INSTALL_SKIP_INFRA=1
      shift
      ;;
    --with-frontend)
      export INSTALL_WITH_FRONTEND=1
      shift
      ;;
    --with-ai-toolstack)
      export INSTALL_WITH_AI_TOOLSTACK=1
      shift
      ;;
    --stage)
      [[ $# -ge 2 ]] || { echo "error: --stage needs a name" >&2; exit 64; }
      MODE="stage"
      STAGE_NAME="$2"
      shift 2
      ;;
    --list-stages)
      MODE="list"
      shift
      ;;
    --compose-timeout)
      [[ $# -ge 2 ]] || { echo "error: --compose-timeout needs seconds" >&2; exit 64; }
      export INSTALL_COMPOSE_TIMEOUT="$2"
      shift 2
      ;;
    --non-interactive)
      export INSTALL_NONINTERACTIVE=1
      shift
      ;;
    *)
      echo "error: unknown option: $1 (try --help)" >&2
      exit 64
      ;;
  esac
done

# shellcheck source=scripts/install/load.sh
source "${LIB}/load.sh"
install_main "${MODE}" "${STAGE_NAME}"
