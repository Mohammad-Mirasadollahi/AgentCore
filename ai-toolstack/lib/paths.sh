# Central paths for ThinkingSOC AI toolstack. Source from scripts/hooks:
#   source "$(dirname "$0")/../lib/paths.sh"
# shellcheck disable=SC2034

_AI_TOOLSTACK_LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AI_TOOLSTACK_ROOT="$(cd "${_AI_TOOLSTACK_LIB}/.." && pwd)"
export REPO_ROOT="$(cd "${AI_TOOLSTACK_ROOT}/.." && pwd)"

export AI_TOOLSTACK_CONFIG="${AI_TOOLSTACK_ROOT}/config"
export AI_TOOLSTACK_DATA="${AI_TOOLSTACK_ROOT}/data"
export AI_TOOLSTACK_HOOKS="${AI_TOOLSTACK_ROOT}/hooks"
export AI_TOOLSTACK_SCRIPTS="${AI_TOOLSTACK_ROOT}/scripts"
export AI_TOOLSTACK_RULES="${AI_TOOLSTACK_ROOT}/rules"
export AI_TOOLSTACK_DOCS="${AI_TOOLSTACK_ROOT}/docs"

export MCP_MEMORY_DIR="${AI_TOOLSTACK_DATA}/mcp-memory"
export AI_TOOLSTACK_LOCAL="${AI_TOOLSTACK_DATA}/local"

export MCP_MEMORY_FILE="${MCP_MEMORY_DIR}/memory.jsonl"

export TOKEN_STATS_DIR="${AI_TOOLSTACK_DATA}/token-stats"
export TOKEN_STATS_EVENTS="${TOKEN_STATS_DIR}/events.jsonl"

export HEADROOM_DIR="${AI_TOOLSTACK_DATA}/headroom"
export HEADROOM_ENV_SH="${AI_TOOLSTACK_CONFIG}/headroom-env.sh"

export RTK_XDG_DATA_HOME="${AI_TOOLSTACK_DATA}/rtk-xdg"

export LEGACY_MCP_MEMORY="${REPO_ROOT}/.mcp-memory"

export AI_TOOLSTACK_AUTO_UPDATE_ENV="${AI_TOOLSTACK_CONFIG}/auto-update.env.sh"
export AI_TOOLSTACK_AUTO_INSTALL_ENV="${AI_TOOLSTACK_CONFIG}/auto-install.env.sh"

load_headroom_env() {
  # shellcheck source=/dev/null
  [[ -f "${HEADROOM_ENV_SH}" ]] && source "${HEADROOM_ENV_SH}"
}

load_auto_update_env() {
  # shellcheck source=/dev/null
  [[ -f "${AI_TOOLSTACK_AUTO_UPDATE_ENV}" ]] && source "${AI_TOOLSTACK_AUTO_UPDATE_ENV}"
}

auto_update_enabled() {
  load_auto_update_env
  [[ "${AI_TOOLSTACK_AUTO_UPDATE:-1}" != "0" ]]
}

load_auto_install_env() {
  # shellcheck source=/dev/null
  [[ -f "${AI_TOOLSTACK_AUTO_INSTALL_ENV}" ]] && source "${AI_TOOLSTACK_AUTO_INSTALL_ENV}"
  # shellcheck source=/dev/null
  [[ -f "${AI_TOOLSTACK_CONFIG}/auto-install.local.env.sh" ]] && source "${AI_TOOLSTACK_CONFIG}/auto-install.local.env.sh"
  if [[ "${AI_TOOLSTACK_PROFILE:-}" == "agentcore" ]]; then
    # shellcheck source=/dev/null
    [[ -f "${AI_TOOLSTACK_CONFIG}/auto-install-agentcore.env.sh" ]] && source "${AI_TOOLSTACK_CONFIG}/auto-install-agentcore.env.sh"
  fi
}

auto_install_enabled() {
  load_auto_install_env
  [[ "${AI_TOOLSTACK_AUTO_INSTALL:-1}" != "0" ]]
}
