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
# Runtime bring-up (SERVER only): venv MCP | docker mcp-gateway. Empty until resolved.
# Canonical values: venv | docker. Legacy alias: host → venv.
INSTALL_RUNTIME="${INSTALL_RUNTIME:-}"
# Install target: client (CLI only) | server (infra + MCP). Empty until resolved.
INSTALL_ROLE="${INSTALL_ROLE:-}"
# Top-level action: install | upgrade. Empty until resolved (interactive asks).
INSTALL_ACTION="${INSTALL_ACTION:-}"
# Skip the "type yes" confirmation (CI / --yes).
INSTALL_ASSUME_YES="${INSTALL_ASSUME_YES:-0}"
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
  [[ -x "${cli}" ]] || fail "agentcore CLI missing at ${cli}"

  # Always persist PATH into the user's shell rc (path install creates rc if missing).
  # AGENTCORE_SHELL_RC overrides auto-detect (.bashrc/.profile or .zshrc).
  if [[ -n "${AGENTCORE_SHELL_RC:-}" ]]; then
    run "${cli}" path install --shell-rc "${AGENTCORE_SHELL_RC}"
  else
    run "${cli}" path install
  fi

  if [[ ! -e "${link}" && ! -L "${link}" ]]; then
    fail "PATH install failed: missing ${link} (agentcore must be on user PATH)"
  fi
  # Current process + child stages see agentcore immediately.
  export PATH="${HOME}/.local/bin:${PATH}"
  if ! command -v agentcore >/dev/null 2>&1; then
    fail "PATH install failed: agentcore not resolvable after exporting ${HOME}/.local/bin"
  fi
  ok "agentcore PATH shim: ${link}"
}

user_cli_on_path() {
  local link="${HOME}/.local/bin/agentcore"
  [[ -e "${link}" || -L "${link}" ]]
}

# Normalize INSTALL_ROLE → client|server.
normalize_install_role() {
  local raw="${1:-}"
  case "${raw}" in
    client|CLIENT) printf '%s\n' "client" ;;
    server|SERVER) printf '%s\n' "server" ;;
    *) return 1 ;;
  esac
}

# Normalize INSTALL_ACTION → install|upgrade.
normalize_install_action() {
  local raw="${1:-}"
  case "${raw}" in
    install|INSTALL|new) printf '%s\n' "install" ;;
    upgrade|UPGRADE|update) printf '%s\n' "upgrade" ;;
    *) return 1 ;;
  esac
}

prompt_install_action() {
  local choice=""
  banner "Install new or upgrade existing?"
  cat <<'EOF'
  1) install — Fresh / full bootstrap (client or server prompts follow)
  2) upgrade — Re-run stages on an existing install (needs prior install-state)

  Tip: non-interactive — bash install.sh --non-interactive …
       force upgrade — bash install.sh --upgrade --yes
EOF
  while true; do
    printf 'Select action [1=install / 2=upgrade] (default: 1): ' >&2
    read -r choice || true
    choice="${choice:-1}"
    case "${choice}" in
      1|install|INSTALL) printf '%s\n' "install"; return 0 ;;
      2|upgrade|UPGRADE) printf '%s\n' "upgrade"; return 0 ;;
      *) warn "Enter 1/install or 2/upgrade" ;;
    esac
  done
}

# Require the operator to type exactly "yes" (unless --yes / --non-interactive).
confirm_install_action() {
  local action="${1:-}"
  local answer=""
  if [[ "${INSTALL_ASSUME_YES}" == "1" || "${INSTALL_NONINTERACTIVE}" == "1" ]]; then
    info "Confirmation skipped (--yes or --non-interactive); proceeding with ${action}"
    return 0
  fi
  if [[ ! -t 0 ]]; then
    fail "refusing ${action} without TTY confirmation; re-run interactively or pass --yes / --non-interactive"
  fi
  banner "Confirm ${action}"
  printf 'Type yes to continue with %s (anything else aborts): ' "${action}" >&2
  read -r answer || true
  if [[ "${answer}" != "yes" ]]; then
    fail "aborted: expected exactly 'yes' (got '${answer:-}')"
  fi
  ok "Confirmed ${action}"
}

# Resolve INSTALL_ACTION (install|upgrade), then require yes confirmation when interactive.
# Optional preferred arg locks the action (e.g. --upgrade → upgrade) but still asks for yes.
resolve_install_action() {
  local resolved=""
  local preferred="${1:-}"

  if [[ -n "${INSTALL_ACTION}" ]]; then
    resolved="$(normalize_install_action "${INSTALL_ACTION}" || true)"
    [[ -n "${resolved}" ]] || fail "invalid INSTALL_ACTION='${INSTALL_ACTION}' (want: install|upgrade)"
  elif [[ "${INSTALL_ACTION_LOCKED:-0}" == "1" && -n "${preferred}" ]]; then
    resolved="$(normalize_install_action "${preferred}" || true)"
    [[ -n "${resolved}" ]] || fail "invalid action '${preferred}' (want: install|upgrade)"
  elif [[ "${INSTALL_NONINTERACTIVE}" != "1" ]] && [[ -t 0 ]]; then
    resolved="$(prompt_install_action)"
  elif [[ -n "${preferred}" ]]; then
    resolved="$(normalize_install_action "${preferred}" || true)"
    [[ -n "${resolved}" ]] || fail "invalid action '${preferred}' (want: install|upgrade)"
  else
    resolved="install"
    info "Non-interactive: default action=install (pass --upgrade for upgrade)"
  fi

  INSTALL_ACTION="${resolved}"
  export INSTALL_ACTION
  confirm_install_action "${INSTALL_ACTION}"
  ok "Install action: ${INSTALL_ACTION}"
}

# Normalize INSTALL_RUNTIME → venv|docker (legacy host → venv).
normalize_install_runtime() {
  local raw="${1:-}"
  case "${raw}" in
    venv|VENV|host|HOST) printf '%s\n' "venv" ;;
    docker|DOCKER) printf '%s\n' "docker" ;;
    *) return 1 ;;
  esac
}

prompt_install_role() {
  local choice=""
  banner "Install client or server?"
  cat <<'EOF'
  1) client — Coding-agent machine: CLI + venv only (no Postgres/Neo4j Compose).
              Next step after install: agentcore connect
  2) server — AgentCore platform host: Compose stores + MCP gateway

  Tip: non-interactive flags — --role client | --role server
       client shortcut: --skip-infra
EOF
  while true; do
    printf 'Select install target [1=client / 2=server] (default: 2): ' >&2
    read -r choice || true
    choice="${choice:-2}"
    case "${choice}" in
      1|client|CLIENT) printf '%s\n' "client"; return 0 ;;
      2|server|SERVER) printf '%s\n' "server"; return 0 ;;
      *) warn "Enter 1/client or 2/server" ;;
    esac
  done
}

prompt_install_runtime() {
  local choice=""
  banner "Choose how the SERVER runs MCP"
  cat <<'EOF'
  Infra (Postgres + Neo4j) always uses Compose on the server. Pick where MCP runs:

  1) venv   — MCP HTTP from this machine's Python .venv (recommended default)
  2) docker — MCP HTTP inside the mcp-gateway Compose container

  (Legacy name for venv was "host"; --runtime host still works as an alias.)
EOF
  while true; do
    printf 'Select SERVER MCP mode [1=venv / 2=docker] (default: 1): ' >&2
    read -r choice || true
    choice="${choice:-1}"
    case "${choice}" in
      1|venv|VENV|host|HOST) printf '%s\n' "venv"; return 0 ;;
      2|docker|DOCKER) printf '%s\n' "docker"; return 0 ;;
      *) warn "Enter 1/venv or 2/docker" ;;
    esac
  done
}

# Resolve INSTALL_ROLE (client|server). Client forces --skip-infra.
# Persists role=<value> in install-state.env.
resolve_install_role() {
  local resolved=""
  local persisted=""

  if [[ -n "${INSTALL_ROLE}" ]]; then
    resolved="$(normalize_install_role "${INSTALL_ROLE}" || true)"
    [[ -n "${resolved}" ]] || fail "invalid --role '${INSTALL_ROLE}' (want: client|server)"
  elif [[ "${INSTALL_SKIP_INFRA}" == "1" ]]; then
    resolved="client"
    info "Install role=client (from --skip-infra)"
  elif [[ -n "${INSTALL_RUNTIME}" ]]; then
    # Explicit server MCP mode implies server install.
    resolved="server"
    info "Install role=server (from --runtime)"
  elif [[ "${INSTALL_NONINTERACTIVE}" != "1" ]] && [[ -t 0 ]]; then
    resolved="$(prompt_install_role)"
  else
    if [[ -f "${INSTALL_STATE_FILE}" ]]; then
      persisted="$(grep -E '^role=' "${INSTALL_STATE_FILE}" 2>/dev/null | tail -1 | cut -d= -f2- || true)"
    fi
    if resolved="$(normalize_install_role "${persisted}" 2>/dev/null)"; then
      info "Using persisted role=${resolved}"
    else
      resolved="server"
      info "Non-interactive install: default role=server (pass --role client for CLI-only)"
    fi
  fi

  INSTALL_ROLE="${resolved}"
  export INSTALL_ROLE
  if [[ "${INSTALL_ROLE}" == "client" ]]; then
    INSTALL_SKIP_INFRA=1
    export INSTALL_SKIP_INFRA
  fi
  ensure_state_dir
  mark_stage "role" "${INSTALL_ROLE}"
  ok "Install role: ${INSTALL_ROLE}"
}

# Resolve INSTALL_RUNTIME from flag, TTY prompt, or default venv.
# Persists choice to install-state.env as runtime=<value>.
resolve_install_runtime() {
  local resolved=""
  local persisted=""

  if [[ "${INSTALL_ROLE:-}" == "client" ]]; then
    # Client never brings up MCP here; keep a stable label for state/check.
    INSTALL_RUNTIME="venv"
    export INSTALL_RUNTIME
    ensure_state_dir
    mark_stage "runtime" "${INSTALL_RUNTIME}"
    ok "Install runtime: venv (client — infra skipped; use agentcore connect next)"
    return 0
  fi

  if [[ -n "${INSTALL_RUNTIME}" ]]; then
    resolved="$(normalize_install_runtime "${INSTALL_RUNTIME}" || true)"
    [[ -n "${resolved}" ]] || fail "invalid --runtime '${INSTALL_RUNTIME}' (want: venv|docker; alias: host→venv)"
  elif [[ "${INSTALL_NONINTERACTIVE}" != "1" ]] && [[ -t 0 ]]; then
    resolved="$(prompt_install_runtime)"
  else
    if [[ -f "${INSTALL_STATE_FILE}" ]]; then
      persisted="$(grep -E '^runtime=' "${INSTALL_STATE_FILE}" 2>/dev/null | tail -1 | cut -d= -f2- || true)"
    fi
    if resolved="$(normalize_install_runtime "${persisted}" 2>/dev/null)"; then
      info "Using persisted runtime=${resolved}"
    else
      resolved="venv"
      info "Non-interactive install: default runtime=venv (pass --runtime docker to override)"
    fi
  fi

  if [[ "${resolved}" == "docker" && "${INSTALL_SKIP_INFRA}" == "1" ]]; then
    fail "runtime=docker requires Compose infra (remove --skip-infra / use --role server)"
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
