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

# Repo-root operator templates (never overwrite existing files).
REPO_ENV_FILE="${AGENTCORE_ROOT}/.env"
REPO_ENV_EXAMPLE="${AGENTCORE_ROOT}/.env.example"
REPO_SYNC_FILE="${AGENTCORE_ROOT}/agentcore.sync.yaml"
REPO_SYNC_EXAMPLE="${AGENTCORE_ROOT}/agentcore.sync.yaml.example"

INSTALL_CHECK_ONLY="${INSTALL_CHECK_ONLY:-0}"
INSTALL_NONINTERACTIVE="${INSTALL_NONINTERACTIVE:-0}"
INSTALL_SKIP_PREREQS="${INSTALL_SKIP_PREREQS:-0}"
INSTALL_SKIP_INFRA="${INSTALL_SKIP_INFRA:-0}"
INSTALL_WITH_FRONTEND="${INSTALL_WITH_FRONTEND:-0}"
INSTALL_WITH_AI_TOOLSTACK="${INSTALL_WITH_AI_TOOLSTACK:-0}"
INSTALL_COMPOSE_TIMEOUT="${INSTALL_COMPOSE_TIMEOUT:-300}"
# Runtime bring-up: host (venv MCP) | docker (mcp-gateway container). Empty until resolved.
INSTALL_RUNTIME="${INSTALL_RUNTIME:-}"
AGENTCORE_WHEELHOUSE="${AGENTCORE_WHEELHOUSE:-/opt/agentcore-wheelhouse}"

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

copy_example_if_missing() {
  local example="$1"
  local dest="$2"
  local label="$3"
  if [[ -f "${dest}" ]]; then
    ok "${label} present: ${dest}"
    return 0
  fi
  require_file "${example}" "missing template ${example}"
  info "Copying ${example} → ${dest}"
  cp "${example}" "${dest}"
  ok "Created ${dest} (edit as needed; re-install will not overwrite)"
}

# Seed repo-root .env and agentcore.sync.yaml from *.example when absent.
seed_repo_operator_files() {
  copy_example_if_missing "${REPO_ENV_EXAMPLE}" "${REPO_ENV_FILE}" "repo .env"
  copy_example_if_missing "${REPO_SYNC_EXAMPLE}" "${REPO_SYNC_FILE}" "agentcore.sync.yaml"
}

# Symlink ~/.local/bin/agentcore and ensure a durable PATH export in shell rc.
install_cli_on_path() {
  local cli="${1:?}"
  local link="${HOME}/.local/bin/agentcore"
  local shell_rc=""
  [[ -x "${cli}" ]] || fail "agentcore CLI missing at ${cli}"

  if [[ -n "${AGENTCORE_SHELL_RC:-}" ]]; then
    shell_rc="${AGENTCORE_SHELL_RC}"
  elif [[ "${SHELL:-}" == */zsh ]] && [[ -f "${HOME}/.zshrc" ]]; then
    shell_rc=".zshrc"
  elif [[ -f "${HOME}/.bashrc" ]]; then
    shell_rc=".bashrc"
  fi

  if [[ -n "${shell_rc}" ]]; then
    run "${cli}" path install --shell-rc "${shell_rc}"
  else
    run "${cli}" path install
  fi

  if [[ ! -e "${link}" && ! -L "${link}" ]]; then
    fail "PATH install failed: missing ${link} (agentcore must be on user PATH)"
  fi
  ok "agentcore PATH shim: ${link}"
}

user_cli_on_path() {
  local link="${HOME}/.local/bin/agentcore"
  [[ -e "${link}" || -L "${link}" ]]
}

# Normalize and validate INSTALL_RUNTIME (host|docker).
normalize_install_runtime() {
  local raw="${1:-}"
  case "${raw}" in
    host|docker) printf '%s\n' "${raw}" ;;
    *) return 1 ;;
  esac
}

prompt_install_runtime() {
  local choice=""
  banner "Choose how to bring AgentCore up"
  cat <<'EOF'
  1) host   — Compose Postgres/Neo4j + MCP HTTP from host .venv (agentcore service start)
  2) docker — Compose Postgres/Neo4j + MCP HTTP in the mcp-gateway container (wheelhouse image)

Both options install OS prerequisites, create .venv, and put `agentcore` on your PATH
(~/.local/bin + shell rc).
EOF
  while true; do
    printf 'Select runtime [1=host / 2=docker] (default: 1): ' >&2
    read -r choice || true
    choice="${choice:-1}"
    case "${choice}" in
      1|host|HOST) printf '%s\n' "host"; return 0 ;;
      2|docker|DOCKER) printf '%s\n' "docker"; return 0 ;;
      *) warn "Enter 1/host or 2/docker" ;;
    esac
  done
}

# Resolve INSTALL_RUNTIME from flag, TTY prompt, or default host.
# Persists choice to install-state.env as runtime=<value>.
resolve_install_runtime() {
  local resolved=""
  local persisted=""

  if [[ -n "${INSTALL_RUNTIME}" ]]; then
    resolved="$(normalize_install_runtime "${INSTALL_RUNTIME}" || true)"
    [[ -n "${resolved}" ]] || fail "invalid --runtime '${INSTALL_RUNTIME}' (want: host|docker)"
  elif [[ "${INSTALL_NONINTERACTIVE}" != "1" ]] && [[ -t 0 ]]; then
    resolved="$(prompt_install_runtime)"
  else
    if [[ -f "${INSTALL_STATE_FILE}" ]]; then
      persisted="$(grep -E '^runtime=' "${INSTALL_STATE_FILE}" 2>/dev/null | tail -1 | cut -d= -f2- || true)"
    fi
    if resolved="$(normalize_install_runtime "${persisted}" 2>/dev/null)"; then
      info "Using persisted runtime=${resolved}"
    else
      resolved="host"
      info "Non-interactive install: default runtime=host (pass --runtime docker to override)"
    fi
  fi

  if [[ "${resolved}" == "docker" && "${INSTALL_SKIP_INFRA}" == "1" ]]; then
    fail "runtime=docker requires Compose infra (remove --skip-infra)"
  fi

  INSTALL_RUNTIME="${resolved}"
  export INSTALL_RUNTIME
  ensure_state_dir
  mark_stage "runtime" "${INSTALL_RUNTIME}"
  ok "Install runtime: ${INSTALL_RUNTIME}"
}

# Always ensure ~/.local/bin is exported for this process and present on disk.
ensure_agentcore_on_path() {
  local venv_cli
  venv_cli="${AGENTCORE_ROOT}/${AGENTCORE_VENV_DIR:-.venv}/bin/agentcore"
  export PATH="${HOME}/.local/bin:${PATH}"
  [[ -x "${venv_cli}" ]] || fail "cannot install PATH: missing ${venv_cli} (stage 02 incomplete)"
  install_cli_on_path "${venv_cli}"
  user_cli_on_path || fail "agentcore still not on user PATH after install"
  ok "PATH ready: ${HOME}/.local/bin/agentcore"
}
