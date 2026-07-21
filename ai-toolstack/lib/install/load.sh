# ai-toolstack install — load all install modules (source after lib/paths.sh).

: "${AI_TOOLSTACK_ROOT:?source lib/paths.sh before lib/install/load.sh}"

_INSTALL_LIB="${AI_TOOLSTACK_ROOT}/lib/install"

# shellcheck source=common.sh
source "${_INSTALL_LIB}/common.sh"
# shellcheck source=resolve-bins.sh
source "${_INSTALL_LIB}/resolve-bins.sh"
# shellcheck source=hooks.sh
source "${_INSTALL_LIB}/hooks.sh"
# shellcheck source=mcp-packages.sh
source "${_INSTALL_LIB}/mcp-packages.sh"
# shellcheck source=mcp-config.sh
source "${_INSTALL_LIB}/mcp-config.sh"
# shellcheck source=cursor-wiring.sh
source "${_INSTALL_LIB}/cursor-wiring.sh"

install_main() {
  local no_verify="${1:-false}"
  local verify_rc=0

  install_chmod_scripts
  install_purge_legacy_graph_paths
  install_repo_symlinks
  install_generated_configs
  install_user_symlinks
  install_global_cursor_rules
  install_global_cursor_skills
  install_cursor_rules
  install_cursor_skills
  install_agents_skills_mirror
  install_cursor_entrypoints
  install_agents_rules_mirror
  install_cursor_agent_manifest || true

  if [[ "${no_verify}" != true ]]; then
    install_run_verify || verify_rc=$?
  else
    ai_toolstack_info "Skipped post-install verification (--no-verify)"
  fi

  install_ensure_mcp_lazy_cache || true

  if [[ "${verify_rc}" -eq 0 ]]; then
    ai_toolstack_info "Install complete."
  else
    ai_toolstack_info "Install finished with verification failures — fix and re-run verify:"
    ai_toolstack_info "  ./ai-toolstack/scripts/verify-install.sh"
    ai_toolstack_info "  ./ai-toolstack/scripts/ai-toolstack.sh verify"
  fi
  ai_toolstack_info "Then: Cursor → Reload Window"
  ai_toolstack_info "Rules + skills inventory: ai-toolstack/cursor-agent-config/MANIFEST.md"
  ai_toolstack_info "Ponytail vendor refresh: ./ai-toolstack/scripts/sync-ponytail-vendor.sh"
  return "${verify_rc}"
}
