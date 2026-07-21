# Resolve node/npm/npx when Cursor's MCP spawn PATH omits nvm/fnm (~/.profile not loaded).
# Source after paths.sh:
#   source "${AI_TOOLSTACK_ROOT}/lib/resolve-node.sh"

NODE_TOOLCHAIN_BIN="${AI_TOOLSTACK_LOCAL}/bin"

_find_node_executable() {
  local name="${1}"
  local candidate ver dir

  candidate="$(command -v "${name}" 2>/dev/null || true)"
  if [[ -n "${candidate}" && -x "${candidate}" && "${candidate}" != "${NODE_TOOLCHAIN_BIN}/${name}" ]]; then
    echo "${candidate}"
    return 0
  fi

  for candidate in "/usr/local/bin/${name}" "/usr/bin/${name}"; do
    if [[ -x "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
  done

  if [[ -d "${HOME}/.nvm/versions/node" ]]; then
    ver="$(ls -1 "${HOME}/.nvm/versions/node" 2>/dev/null | sort -V | tail -1 || true)"
    if [[ -n "${ver}" ]]; then
      candidate="${HOME}/.nvm/versions/node/${ver}/bin/${name}"
      if [[ -x "${candidate}" ]]; then
        echo "${candidate}"
        return 0
      fi
    fi
  fi

  if [[ -d "${HOME}/.fnm/node-versions" ]]; then
    ver="$(ls -1 "${HOME}/.fnm/node-versions" 2>/dev/null | sort -V | tail -1 || true)"
    if [[ -n "${ver}" ]]; then
      candidate="${HOME}/.fnm/node-versions/${ver}/installation/bin/${name}"
      if [[ -x "${candidate}" ]]; then
        echo "${candidate}"
        return 0
      fi
    fi
  fi

  if [[ -d "${HOME}/.asdf/shims" ]]; then
    candidate="${HOME}/.asdf/shims/${name}"
    if [[ -x "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
  fi

  return 1
}

_toolchain_executable() {
  local name="${1}"
  local path="${NODE_TOOLCHAIN_BIN}/${name}"
  if [[ -x "${path}" ]]; then
    echo "${path}"
    return 0
  fi
  _find_node_executable "${name}"
}

_link_node_toolchain_bin() {
  local name="${1}"
  local src="${2}"
  local dest="${NODE_TOOLCHAIN_BIN}/${name}"

  if [[ -z "${src}" || ! -x "${src}" ]]; then
    return 1
  fi

  mkdir -p "${NODE_TOOLCHAIN_BIN}"
  ln -sfn "${src}" "${dest}"
  return 0
}

# Populate ${AI_TOOLSTACK_LOCAL}/bin/{node,npm,npx} symlinks from the best available install.
# Returns 0 when npx is resolvable (required for mcp-lazy).
ensure_node_toolchain() {
  local node_src npm_src npx_src

  npx_src="$(_find_node_executable npx)" || return 1
  npm_src="$(_find_node_executable npm)" || npm_src=""
  node_src="$(_find_node_executable node)" || node_src=""

  _link_node_toolchain_bin npx "${npx_src}" || return 1
  [[ -n "${npm_src}" ]] && _link_node_toolchain_bin npm "${npm_src}" || true
  [[ -n "${node_src}" ]] && _link_node_toolchain_bin node "${node_src}" || true
  return 0
}

resolve_npx() {
  ensure_node_toolchain >/dev/null 2>&1 || true
  _toolchain_executable npx
}

resolve_npm() {
  ensure_node_toolchain >/dev/null 2>&1 || true
  _toolchain_executable npm
}
