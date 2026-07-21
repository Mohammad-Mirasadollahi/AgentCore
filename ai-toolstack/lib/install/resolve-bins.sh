# ai-toolstack install — resolve headroom / rtk binaries.

install_resolve_headroom_bin() {
  for c in "${HEADROOM_BIN:-}" "${HOME}/.local/bin/headroom" \
    "${HOME}/.local/share/pipx/venvs/headroom-ai/bin/headroom"; do
    [[ -n "${c}" && -x "${c}" ]] && echo "${c}" && return 0
  done
  command -v headroom 2>/dev/null || echo "headroom"
}

install_resolve_rtk_bin() {
  for c in "${RTK_BIN:-}" "${HOME}/.local/bin/rtk" "/usr/local/bin/rtk"; do
    [[ -n "${c}" && -x "${c}" ]] && echo "${c}" && return 0
  done
  command -v rtk 2>/dev/null || true
}
