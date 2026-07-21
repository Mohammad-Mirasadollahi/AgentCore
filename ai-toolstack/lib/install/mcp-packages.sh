# ai-toolstack install — local MCP / Headroom package installs and patches.

: "${AI_TOOLSTACK_ROOT:?source lib/paths.sh first}"

# shellcheck source=../resolve-node.sh
source "${AI_TOOLSTACK_ROOT}/lib/resolve-node.sh"
# shellcheck source=resolve-bins.sh
source "${AI_TOOLSTACK_ROOT}/lib/install/resolve-bins.sh"

MCP_LAZY_SERVE="${AI_TOOLSTACK_ROOT}/bin/mcp-lazy-serve.sh"
HEADROOM_MCP_SERVE="${AI_TOOLSTACK_ROOT}/bin/headroom-mcp-serve.sh"

HEADROOM_PKG="headroom-ai"
HEADROOM_PKG_EXTRAS="[mcp]"

MCP_MEMORY_PKG="@modelcontextprotocol/server-memory"
MCP_MEMORY_PKG_VERSION="2026.1.26"
MCP_LAZY_PKG="mcp-lazy"
MCP_LAZY_PKG_VERSION="0.1.7"

MCP_MEMORY_CMD="npx"
MCP_MEMORY_ARGS="\"-y\", \"${MCP_MEMORY_PKG}\""

install_ensure_memory_server() {
  local bin="${AI_TOOLSTACK_LOCAL}/node_modules/.bin/mcp-server-memory"
  local npm_bin
  npm_bin="$(resolve_npm 2>/dev/null || true)"
  if [[ ! -x "${bin}" && -n "${npm_bin}" && -x "${npm_bin}" ]]; then
    ai_toolstack_info "Installing ${MCP_MEMORY_PKG}@${MCP_MEMORY_PKG_VERSION} locally (avoids npx startup timeout)"
    install_ensure_dir "${AI_TOOLSTACK_LOCAL}"
    if [[ ! -f "${AI_TOOLSTACK_LOCAL}/package.json" ]]; then
      (cd "${AI_TOOLSTACK_LOCAL}" && npm init -y >/dev/null 2>&1) || true
    fi
    (cd "${AI_TOOLSTACK_LOCAL}" \
      && "${npm_bin}" install --no-fund --no-audit "${MCP_MEMORY_PKG}@${MCP_MEMORY_PKG_VERSION}" >/dev/null 2>&1) \
      || ai_toolstack_warn "local memory install failed — falling back to npx"
  fi
  if [[ -x "${bin}" ]]; then
    MCP_MEMORY_CMD="${bin}"
    MCP_MEMORY_ARGS=""
  else
    MCP_MEMORY_CMD="$(resolve_npx 2>/dev/null || echo npx)"
    MCP_MEMORY_ARGS="\"-y\", \"${MCP_MEMORY_PKG}\""
  fi
  export MCP_MEMORY_CMD MCP_MEMORY_ARGS
}

install_ensure_mcp_lazy_server() {
  local bin="${AI_TOOLSTACK_LOCAL}/node_modules/.bin/mcp-lazy"
  local index_js="${AI_TOOLSTACK_LOCAL}/node_modules/mcp-lazy/dist/index.js"
  local patch_py="${AI_TOOLSTACK_SCRIPTS}/patch-mcp-lazy-debug.py"
  local npm_bin
  npm_bin="$(resolve_npm 2>/dev/null || true)"
  if [[ ! -x "${bin}" && -n "${npm_bin}" && -x "${npm_bin}" ]]; then
    ai_toolstack_info "Installing ${MCP_LAZY_PKG}@${MCP_LAZY_PKG_VERSION} locally (avoids npx startup hang)"
    install_ensure_dir "${AI_TOOLSTACK_LOCAL}"
    if [[ ! -f "${AI_TOOLSTACK_LOCAL}/package.json" ]]; then
      (cd "${AI_TOOLSTACK_LOCAL}" && npm init -y >/dev/null 2>&1) || true
    fi
    (cd "${AI_TOOLSTACK_LOCAL}" \
      && "${npm_bin}" install --no-fund --no-audit "${MCP_LAZY_PKG}@${MCP_LAZY_PKG_VERSION}" >/dev/null 2>&1) \
      || ai_toolstack_warn "local mcp-lazy install failed — falling back to npx -y mcp-lazy"
  fi
  if [[ -f "${index_js}" && -f "${patch_py}" ]]; then
    if python3 "${patch_py}" "${index_js}"; then
      ai_toolstack_info "mcp-lazy debug patch applied (set MCP_LAZY_VERBOSE=1 to enable verbose logs)"
    else
      ai_toolstack_warn "mcp-lazy debug patch failed (upgrade may have changed dist/index.js)"
    fi
  elif [[ ! -f "${index_js}" ]]; then
    ai_toolstack_warn "mcp-lazy dist/index.js not found — skip debug patch"
  fi
  local stats_patch="${AI_TOOLSTACK_SCRIPTS}/patch-mcp-lazy-token-stats.py"
  if [[ -f "${index_js}" && -f "${stats_patch}" ]]; then
    if python3 "${stats_patch}" "${index_js}"; then
      ai_toolstack_info "mcp-lazy token-stats patch applied"
    else
      ai_toolstack_warn "mcp-lazy token-stats patch failed"
    fi
  fi
  local aliases_patch="${AI_TOOLSTACK_SCRIPTS}/patch-mcp-lazy-execute-aliases.py"
  if [[ -f "${index_js}" && -f "${aliases_patch}" ]]; then
    if python3 "${aliases_patch}" "${index_js}"; then
      ai_toolstack_info "mcp-lazy execute-aliases patch applied (server/tool + flat args)"
    else
      ai_toolstack_warn "mcp-lazy execute-aliases patch failed"
    fi
  fi
  install_ensure_dir "${AI_TOOLSTACK_DATA}/mcp-lazy/logs"
  install_ensure_dir "${AI_TOOLSTACK_DATA}/token-stats"
}

install_ensure_headroom_server() {
  local headroom_bin
  headroom_bin="$(install_resolve_headroom_bin)"
  if [[ ! -x "${headroom_bin}" || "${headroom_bin}" == "headroom" ]]; then
    if command -v pipx >/dev/null 2>&1; then
      ai_toolstack_info "Installing ${HEADROOM_PKG}${HEADROOM_PKG_EXTRAS} via pipx (Headroom MCP)..."
      if pipx install "${HEADROOM_PKG}${HEADROOM_PKG_EXTRAS}" --python python3.12 >/dev/null 2>&1; then
        ai_toolstack_info "Headroom installed"
      else
        ai_toolstack_warn "pipx install ${HEADROOM_PKG} failed — run: pipx install '${HEADROOM_PKG}${HEADROOM_PKG_EXTRAS}'"
      fi
    else
      ai_toolstack_warn "pipx not found — install Headroom manually: pipx install '${HEADROOM_PKG}${HEADROOM_PKG_EXTRAS}'"
    fi
  fi
  headroom_bin="$(install_resolve_headroom_bin)"
  if [[ -x "${headroom_bin}" && "${headroom_bin}" != "headroom" ]]; then
    ai_toolstack_info "Headroom MCP ready (${headroom_bin})"
  else
    ai_toolstack_warn "headroom CLI not found — Headroom MCP backend will be skipped by mcp-lazy init"
  fi
  install_ensure_dir "${HEADROOM_DIR}" "${HEADROOM_DIR}/logs"
  if [[ -f "${HEADROOM_MCP_SERVE}" ]]; then
    chmod +x "${HEADROOM_MCP_SERVE}"
  fi
}
