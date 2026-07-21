# ai-toolstack install — generated MCP configs and mcp-lazy cache refresh.

install_mcp_json() {
  local template="${AI_TOOLSTACK_CONFIG}/mcp.json.template"
  local output="${AI_TOOLSTACK_LOCAL}/mcp.json"
  if [[ ! -f "${template}" ]]; then
    ai_toolstack_warn "mcp.json.template missing — skip MCP config generation"
    return 1
  fi
  mkdir -p "$(dirname "${output}")"
  sed \
    -e "s|@MCP_LAZY_SERVE@|${MCP_LAZY_SERVE}|g" \
    -e "s|@HEADROOM_MCP_SERVE@|${HEADROOM_MCP_SERVE}|g" \
    -e "s|@HEADROOM_DIR@|${HEADROOM_DIR}|g" \
    -e "s|@REPO_ROOT@|${REPO_ROOT}|g" \
    "${template}" > "${output}"
}

install_generated_configs() {
  # shellcheck source=../../scripts/ensure-host-deps.sh
  source "${AI_TOOLSTACK_SCRIPTS}/ensure-host-deps.sh"
  ensure_host_deps
  ensure_node_toolchain || ai_toolstack_warn "node/npx not found — install Node.js then re-run install.sh"
  install_ensure_memory_server
  install_ensure_mcp_lazy_server
  install_ensure_headroom_server
  install_mcp_json || true
  install_substitute_template \
    "${AI_TOOLSTACK_CONFIG}/mcp-lazy-servers.json.template" \
    "${AI_TOOLSTACK_LOCAL}/mcp-lazy-servers.json"
  install_substitute_template \
    "${AI_TOOLSTACK_CONFIG}/cursor-hooks.json.template" \
    "${AI_TOOLSTACK_LOCAL}/cursor-hooks.json"
  install_apply_rtk_shell_hook
  install_apply_ponytail_output_hook
}

install_ensure_mcp_lazy_cache() {
  local -a mcp_lazy_cmd=()
  local npx_bin
  if ! ensure_node_toolchain; then
    ai_toolstack_warn "node/npx not found — skip mcp-lazy init (MCP will fail until Node is installed)"
    return 1
  fi
  npx_bin="${NODE_TOOLCHAIN_BIN}/npx"
  export PATH="${NODE_TOOLCHAIN_BIN}:${PATH}"
  if [[ -x "${AI_TOOLSTACK_LOCAL}/node_modules/.bin/mcp-lazy" ]]; then
    mcp_lazy_cmd=("${AI_TOOLSTACK_LOCAL}/node_modules/.bin/mcp-lazy")
  else
    mcp_lazy_cmd=("${npx_bin}" "-y" "mcp-lazy")
  fi
  ai_toolstack_info "Refreshing mcp-lazy tool cache..."
  if timeout 120 env MCP_LAZY_VERBOSE=0 MCP_LAZY_DEBUG=0 MCP_LAZY_LOG_DIR="${AI_TOOLSTACK_DATA}/mcp-lazy/logs" \
    "${mcp_lazy_cmd[@]}" init >/dev/null 2>&1; then
    ai_toolstack_info "mcp-lazy cache ready (memory + headroom backends)"
    return 0
  fi
  ai_toolstack_warn "mcp-lazy init failed — run: ./ai-toolstack/scripts/mcp-lazy-diagnose.sh"
  return 1
}

install_repo_symlinks() {
  install_migrate_dir_to_data "${LEGACY_MCP_MEMORY}" "${MCP_MEMORY_DIR}"
  install_ensure_dir "${MCP_MEMORY_DIR}" "${AI_TOOLSTACK_LOCAL}" "${HEADROOM_DIR}"
  install_link_path "${MCP_MEMORY_DIR}" "${LEGACY_MCP_MEMORY}"
}

install_user_symlinks() {
  install_link_path "${AI_TOOLSTACK_LOCAL}/mcp.json" "${HOME}/.cursor/mcp.json"
  install_link_path "${AI_TOOLSTACK_LOCAL}/mcp-lazy-servers.json" "${HOME}/.mcp-lazy/servers.json"
  install_link_path "${AI_TOOLSTACK_LOCAL}/cursor-hooks.json" "${HOME}/.cursor/hooks.json"
}
