# ai-toolstack install — Cursor hooks.json (RTK + ponytail stats).

install_apply_rtk_shell_hook() {
  local hooks_file="${AI_TOOLSTACK_LOCAL}/cursor-hooks.json"
  if [[ ! -f "${hooks_file}" ]]; then
    return 0
  fi
  if [[ "${AI_TOOLSTACK_RTK_HOOK:-1}" == "0" ]]; then
    ai_toolstack_info "RTK Shell hook disabled (AI_TOOLSTACK_RTK_HOOK=0)"
    if command -v jq >/dev/null 2>&1; then
      jq '.hooks.preToolUse = []' "${hooks_file}" > "${hooks_file}.tmp"
      mv "${hooks_file}.tmp" "${hooks_file}"
    fi
    return 0
  fi
  local hook_script="${AI_TOOLSTACK_HOOKS}/rtk-cursor-hook.sh"
  if [[ ! -x "${hook_script}" ]]; then
    ai_toolstack_warn "rtk-cursor-hook.sh missing — skip RTK Shell hook"
    return 0
  fi
  if ! command -v jq >/dev/null 2>&1; then
    ai_toolstack_warn "jq missing — cannot enable RTK Shell hook"
    return 0
  fi
  local rtk_bin
  rtk_bin="$(install_resolve_rtk_bin || true)"
  if [[ -z "${rtk_bin}" || ! -x "${rtk_bin}" ]]; then
    ai_toolstack_warn "rtk not on PATH — RTK Shell hook not enabled (set AI_TOOLSTACK_AUTO_INSTALL_RTK=1 and re-run install)"
    jq '.hooks.preToolUse = []' "${hooks_file}" > "${hooks_file}.tmp"
    mv "${hooks_file}.tmp" "${hooks_file}"
    return 0
  fi
  jq --arg cmd "${hook_script}" \
    '.hooks.preToolUse = [{"matcher": "Shell", "command": $cmd, "timeout": 120}]' \
    "${hooks_file}" > "${hooks_file}.tmp"
  mv "${hooks_file}.tmp" "${hooks_file}"
  ai_toolstack_info "RTK Shell hook enabled (${hook_script}) — watermark + Headroom bypass guard"
}

install_apply_ponytail_output_hook() {
  local hooks_file="${AI_TOOLSTACK_LOCAL}/cursor-hooks.json"
  if [[ ! -f "${hooks_file}" ]]; then
    return 0
  fi
  if [[ "${AI_TOOLSTACK_PONYTAIL_STATS_HOOK:-1}" == "0" ]]; then
    ai_toolstack_info "Ponytail output-stats hook disabled (AI_TOOLSTACK_PONYTAIL_STATS_HOOK=0)"
    return 0
  fi
  local hook_script="${AI_TOOLSTACK_HOOKS}/ponytail-output-stats.sh"
  chmod +x "${hook_script}" 2>/dev/null || true
  if [[ ! -f "${hook_script}" ]]; then
    ai_toolstack_warn "ponytail-output-stats.sh missing — skip output stats hook"
    return 0
  fi
  if ! command -v jq >/dev/null 2>&1; then
    ai_toolstack_warn "jq missing — cannot enable ponytail output-stats hook"
    return 0
  fi
  jq --arg cmd "${hook_script}" \
    '.hooks.afterAgentResponse = [{"command": $cmd, "timeout": 15}]' \
    "${hooks_file}" > "${hooks_file}.tmp"
  mv "${hooks_file}.tmp" "${hooks_file}"
  ai_toolstack_info "Ponytail output-stats hook enabled (${hook_script})"
}
