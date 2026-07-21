# ai-toolstack install — shared helpers (source after lib/paths.sh).
# shellcheck disable=SC2034

: "${AI_TOOLSTACK_ROOT:?source lib/paths.sh first}"

ai_toolstack_info() { echo "[ai-toolstack] $*"; }
ai_toolstack_warn() { echo "[ai-toolstack] WARN: $*" >&2; }

install_ensure_dir() {
  mkdir -p "${1}"
}

install_link_path() {
  local source="${1}"
  local dest="${2}"
  install_ensure_dir "$(dirname "${dest}")"
  # ln -sfn into an existing *directory* nests the link inside it; always replace.
  if [[ -e "${dest}" || -L "${dest}" ]]; then
    rm -rf "${dest}"
  fi
  ln -sfn "${source}" "${dest}"
}

install_migrate_dir_to_data() {
  local legacy="${1}"
  local target="${2}"
  install_ensure_dir "${target}"
  if [[ -L "${legacy}" ]]; then
    return 0
  fi
  if [[ -d "${legacy}" ]]; then
    ai_toolstack_info "Migrating ${legacy} -> ${target}"
    shopt -s dotglob nullglob
    local entries=("${legacy}"/*)
    shopt -u dotglob nullglob
    if [[ ${#entries[@]} -gt 0 ]]; then
      cp -a "${legacy}/." "${target}/"
      rm -rf "${legacy}"
    else
      rmdir "${legacy}" 2>/dev/null || rm -rf "${legacy}"
    fi
  fi
}

install_substitute_template() {
  local template="${1}"
  local output="${2}"

  mkdir -p "$(dirname "${output}")"
  sed \
    -e "s|@REPO_ROOT@|${REPO_ROOT}|g" \
    -e "s|@MCP_MEMORY_FILE@|${MCP_MEMORY_FILE}|g" \
    -e "s|@HOOKS_DIR@|${AI_TOOLSTACK_HOOKS}|g" \
    -e "s|@MCP_MEMORY_CMD@|${MCP_MEMORY_CMD}|g" \
    -e "s|@MCP_MEMORY_ARGS@|${MCP_MEMORY_ARGS}|g" \
    -e "s|@MCP_LAZY_SERVE@|${MCP_LAZY_SERVE}|g" \
    -e "s|@HEADROOM_MCP_SERVE@|${HEADROOM_MCP_SERVE}|g" \
    -e "s|@HEADROOM_DIR@|${HEADROOM_DIR}|g" \
    "${template}" > "${output}"
}

install_purge_legacy_graph_paths() {
  local purge="${AI_TOOLSTACK_SCRIPTS}/purge-legacy-graph-paths.sh"
  if [[ -x "${purge}" ]]; then
    "${purge}" || ai_toolstack_warn "purge-legacy-graph-paths.sh reported errors"
  else
    ai_toolstack_warn "purge-legacy-graph-paths.sh missing — skip legacy graph dir cleanup"
  fi
}

install_chmod_scripts() {
  chmod +x "${AI_TOOLSTACK_HOOKS}"/*.sh "${AI_TOOLSTACK_SCRIPTS}"/*.sh "${AI_TOOLSTACK_ROOT}/bin/"*.sh \
    "${AI_TOOLSTACK_ROOT}/install.sh" 2>/dev/null || true
  [[ -f "${AI_TOOLSTACK_SCRIPTS}/ensure-host-deps.sh" ]] && chmod +x "${AI_TOOLSTACK_SCRIPTS}/ensure-host-deps.sh"
  [[ -f "${AI_TOOLSTACK_SCRIPTS}/verify-install.sh" ]] && chmod +x "${AI_TOOLSTACK_SCRIPTS}/verify-install.sh"
  [[ -f "${AI_TOOLSTACK_SCRIPTS}/purge-legacy-graph-paths.sh" ]] && chmod +x "${AI_TOOLSTACK_SCRIPTS}/purge-legacy-graph-paths.sh"
}

install_print_check() {
  echo "REPO_ROOT=${REPO_ROOT}"
  echo "AI_TOOLSTACK_ROOT=${AI_TOOLSTACK_ROOT}"
  echo "MCP_MEMORY_FILE=${MCP_MEMORY_FILE}"
  echo "HEADROOM_DIR=${HEADROOM_DIR}"
  echo "~/.cursor/mcp.json -> $(readlink -f "${HOME}/.cursor/mcp.json" 2>/dev/null || echo missing)"
  echo "~/.mcp-lazy/servers.json -> $(readlink -f "${HOME}/.mcp-lazy/servers.json" 2>/dev/null || echo missing)"
}

install_run_verify() {
  local verify="${AI_TOOLSTACK_SCRIPTS}/verify-install.sh"
  if [[ ! -x "${verify}" ]]; then
    ai_toolstack_warn "verify-install.sh missing — skip post-check"
    return 0
  fi
  ai_toolstack_info "Running post-install verification..."
  if "${verify}"; then
    return 0
  fi
  ai_toolstack_warn "Post-install verification reported failures (see above)"
  return 1
}
