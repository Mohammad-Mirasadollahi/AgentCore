# Shared helpers for AgentCore modular install.
# Sourced by load.sh — do not execute directly.
# shellcheck shell=bash

: "${AGENTCORE_ROOT:?AGENTCORE_ROOT must be set}"

INSTALL_LOG_PREFIX="${INSTALL_LOG_PREFIX:-[agentcore-install]}"
INSTALL_STATE_DIR="${AGENTCORE_ROOT}/.agentcore"
INSTALL_STATE_FILE="${INSTALL_STATE_DIR}/install-state.env"
COMPOSE_DIR="${AGENTCORE_ROOT}/backend/deployments/compose"
COMPOSE_FILE="${COMPOSE_DIR}/compose.yaml"
COMPOSE_ENV_FILE="${COMPOSE_DIR}/.env.local"
COMPOSE_ENV_EXAMPLE="${COMPOSE_DIR}/neo4j.example.env"
WAIT_HEALTHY="${COMPOSE_DIR}/wait-healthy.sh"

INSTALL_CHECK_ONLY="${INSTALL_CHECK_ONLY:-0}"
INSTALL_NONINTERACTIVE="${INSTALL_NONINTERACTIVE:-1}"
INSTALL_SKIP_PREREQS="${INSTALL_SKIP_PREREQS:-0}"
INSTALL_SKIP_INFRA="${INSTALL_SKIP_INFRA:-0}"
INSTALL_WITH_FRONTEND="${INSTALL_WITH_FRONTEND:-0}"
INSTALL_WITH_AI_TOOLSTACK="${INSTALL_WITH_AI_TOOLSTACK:-0}"
INSTALL_COMPOSE_TIMEOUT="${INSTALL_COMPOSE_TIMEOUT:-180}"

log() { printf '%s %s\n' "${INSTALL_LOG_PREFIX}" "$*"; }
info() { log "INFO  $*"; }
ok() { log "OK    $*"; }
warn() { log "WARN  $*" >&2; }
fail() {
  log "FAIL  $*" >&2
  exit 1
}

banner() {
  local title="$1"
  log "================================================================"
  log "${title}"
  log "================================================================"
}

run() {
  info "→ $*"
  "$@"
}

as_root() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    fail "need root or sudo to run: $*"
  fi
}

have_cmd() { command -v "$1" >/dev/null 2>&1; }

python_bin() {
  local candidate
  for candidate in python3.12 python3; do
    if have_cmd "${candidate}" \
      && "${candidate}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

linux_debian_family() {
  [[ -f /etc/os-release ]] || return 1
  grep -qE '^(ID=debian|ID=ubuntu|ID_LIKE=.*(debian|ubuntu))' /etc/os-release
}

ensure_state_dir() {
  mkdir -p "${INSTALL_STATE_DIR}"
}

mark_stage() {
  local stage="$1"
  local status="${2:-ok}"
  ensure_state_dir
  touch "${INSTALL_STATE_FILE}"
  if grep -q "^${stage}=" "${INSTALL_STATE_FILE}" 2>/dev/null; then
    # portable in-place replace without relying on GNU sed -i semantics alone
    local tmp
    tmp="$(mktemp)"
    grep -v "^${stage}=" "${INSTALL_STATE_FILE}" >"${tmp}" || true
    printf '%s=%s\n' "${stage}" "${status}" >>"${tmp}"
    mv "${tmp}" "${INSTALL_STATE_FILE}"
  else
    printf '%s=%s\n' "${stage}" "${status}" >>"${INSTALL_STATE_FILE}"
  fi
}

stage_status() {
  local stage="$1"
  [[ -f "${INSTALL_STATE_FILE}" ]] || return 1
  grep -E "^${stage}=" "${INSTALL_STATE_FILE}" 2>/dev/null | tail -1 | cut -d= -f2-
}

require_file() {
  local path="$1"
  local hint="${2:-}"
  [[ -f "${path}" ]] || fail "missing file: ${path}${hint:+ — ${hint}}"
}

suggest_fix() {
  local msg="$1"
  warn "fix: ${msg}"
}

random_secret() {
  if have_cmd openssl; then
    openssl rand -hex 24
    return 0
  fi
  # Fallback: urandom hex (48 chars)
  head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n'
}

env_key_value() {
  local file="$1"
  local key="$2"
  [[ -f "${file}" ]] || return 1
  # shellcheck disable=SC2002
  grep -E "^${key}=" "${file}" 2>/dev/null | tail -1 | cut -d= -f2-
}

env_has_placeholder_secret() {
  local file="$1"
  local key="$2"
  local val
  val="$(env_key_value "${file}" "${key}" || true)"
  [[ -z "${val}" ]] && return 0
  [[ "${val}" == "replace-with-a-local-secret" ]] && return 0
  [[ "${val}" == "changeme" ]] && return 0
  return 1
}
