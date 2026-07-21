#!/usr/bin/env bash
# Install missing host tools for ai-toolstack (jq, pipx, RTK, optional Node).
# Sourced by ai-toolstack/lib/install/mcp-config.sh (via install.sh) — do not run standalone unless debugging.
set -euo pipefail

: "${AI_TOOLSTACK_ROOT:?AI_TOOLSTACK_ROOT required}"
: "${AI_TOOLSTACK_CONFIG:?AI_TOOLSTACK_CONFIG required}"

# shellcheck source=../lib/paths.sh
source "${AI_TOOLSTACK_ROOT}/lib/paths.sh"

_ensure_info() { echo "[ai-toolstack] $*"; }
_ensure_warn() { echo "[ai-toolstack] WARN: $*" >&2; }

_auto_install_flag() {
  local key="${1}"
  local default="${2:-1}"
  load_auto_install_env
  if [[ "${AI_TOOLSTACK_AUTO_INSTALL:-1}" == "0" ]]; then
    return 1
  fi
  local val
  val="$(eval "echo \${${key}:-${default}}")"
  [[ "${val}" != "0" ]]
}

_has_apt() {
  command -v apt-get >/dev/null 2>&1
}

_can_apt_install() {
  _has_apt && [[ "${EUID:-$(id -u)}" -eq 0 ]]
}

_rtk_install_tarball() {
  local ver="${1:?}"
  local arch="${2:?}"
  local tmp="${3:?}"
  local asset="rtk-x86_64-unknown-linux-musl.tar.gz"
  if [[ "${arch}" == "aarch64" || "${arch}" == "arm64" ]]; then
    asset="rtk-aarch64-unknown-linux-gnu.tar.gz"
  fi
  local url="https://github.com/rtk-ai/rtk/releases/download/v${ver}/${asset}"
  _ensure_info "Installing RTK ${ver} (${asset})..."
  curl -fsSL "${url}" -o "${tmp}/${asset}"
  tar -xzf "${tmp}/${asset}" -C "${tmp}"
  mkdir -p "${HOME}/.local/bin"
  local bin
  bin="$(find "${tmp}" -name rtk -type f -executable 2>/dev/null | head -1)"
  [[ -n "${bin}" ]] && install -m 0755 "${bin}" "${HOME}/.local/bin/rtk"
}

ensure_jq() {
  command -v jq >/dev/null 2>&1 && return 0
  _auto_install_flag AI_TOOLSTACK_AUTO_INSTALL_JQ || {
    _ensure_warn "jq not found — install jq or set AI_TOOLSTACK_AUTO_INSTALL_JQ=1"
    return 0
  }
  if _can_apt_install; then
    _ensure_info "Installing jq (apt)..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq jq
    return 0
  fi
  if _has_apt; then
    _ensure_warn "jq missing — run install as root for apt, or install jq manually"
    return 0
  fi
  _ensure_warn "jq missing and apt-get unavailable — install jq manually"
}

ensure_pipx() {
  command -v pipx >/dev/null 2>&1 && return 0
  _auto_install_flag AI_TOOLSTACK_AUTO_INSTALL_PIPX || {
    _ensure_warn "pipx not found — install pipx or set AI_TOOLSTACK_AUTO_INSTALL_PIPX=1"
    return 0
  }
  if _can_apt_install; then
    _ensure_info "Installing pipx (apt)..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq pipx python3-venv
    pipx ensurepath 2>/dev/null || true
    return 0
  fi
  if _has_apt; then
    _ensure_warn "pipx missing — run install as root for apt, or install pipx manually"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    _ensure_info "Installing pipx (pip --user)..."
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath 2>/dev/null || true
    return 0
  fi
  _ensure_warn "pipx missing — install manually for Headroom auto-install"
}

ensure_node_optional() {
  command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1 && return 0
  _auto_install_flag AI_TOOLSTACK_AUTO_INSTALL_NODE 0 || {
    _ensure_warn "node/npm not found — install Node 20+ or set AI_TOOLSTACK_AUTO_INSTALL_NODE=1"
    return 0
  }
  if [[ -n "${NODE_INSTALL_CMD:-}" ]]; then
    _ensure_info "Installing Node (NODE_INSTALL_CMD)..."
    eval "${NODE_INSTALL_CMD}"
    return 0
  fi
  if ! _can_apt_install; then
    _ensure_warn "node/npm missing — install Node 20+ manually, set NODE_INSTALL_CMD, or re-run install as root"
    return 0
  fi
  if [[ "${AI_TOOLSTACK_ALLOW_NODESOURCE:-1}" == "0" ]]; then
    _ensure_warn "node/npm missing — AI_TOOLSTACK_ALLOW_NODESOURCE=0; install Node manually or set NODE_INSTALL_CMD"
    return 0
  fi
  _ensure_info "Installing Node.js 20.x (NodeSource setup script + apt)..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg
  local tmp setup_url
  tmp="$(mktemp -d)"
  setup_url="${NODESETUP_URL:-https://deb.nodesource.com/setup_20.x}"
  curl -fsSL "${setup_url}" -o "${tmp}/nodesource-setup.sh"
  bash "${tmp}/nodesource-setup.sh" || {
    rm -rf "${tmp}"
    _ensure_warn "NodeSource setup failed — install Node manually or set NODE_INSTALL_CMD"
    return 0
  }
  rm -rf "${tmp}"
  apt-get install -y -qq nodejs || {
    _ensure_warn "nodejs apt install failed after NodeSource setup"
    return 0
  }
}

ensure_rtk() {
  # resolve_rtk_bin: ai-toolstack/lib/install/resolve-bins.sh (duplicate minimal lookup when not sourced via install):
  local rtk=""
  for c in "${RTK_BIN:-}" "${HOME}/.local/bin/rtk" "/usr/local/bin/rtk"; do
    [[ -n "${c}" && -x "${c}" ]] && rtk="${c}" && break
  done
  if [[ -z "${rtk}" ]]; then
    rtk="$(command -v rtk 2>/dev/null || true)"
  fi
  if [[ -n "${rtk}" && -x "${rtk}" ]]; then
    return 0
  fi

  _auto_install_flag AI_TOOLSTACK_AUTO_INSTALL_RTK || {
    _ensure_warn "rtk not found — Shell hook disabled unless you install rtk or set AI_TOOLSTACK_AUTO_INSTALL_RTK=1"
    return 0
  }

  if [[ -n "${RTK_INSTALL_CMD:-}" ]]; then
    _ensure_info "Installing RTK (RTK_INSTALL_CMD)..."
    eval "${RTK_INSTALL_CMD}" || _ensure_warn "RTK_INSTALL_CMD failed — continuing without rtk"
  else
    load_auto_install_env
    local ver="${RTK_VERSION:-0.43.0}"
    local arch
    arch="$(uname -m)"
    local tmp
    tmp="$(mktemp -d)"
    local deb_ok=0
    if _can_apt_install && [[ "${arch}" == "x86_64" || "${arch}" == "amd64" ]]; then
      local deb="rtk_${ver}-1_amd64.deb"
      local url="https://github.com/rtk-ai/rtk/releases/download/v${ver}/${deb}"
      _ensure_info "Installing RTK ${ver} (${deb})..."
      if curl -fsSL "${url}" -o "${tmp}/${deb}"; then
        if dpkg -i "${tmp}/${deb}" 2>/dev/null \
          || apt-get install -y -f -qq; then
          deb_ok=1
        else
          _ensure_warn "RTK .deb install failed — falling back to user tarball (~/.local/bin)"
        fi
      else
        _ensure_warn "RTK .deb download failed — falling back to user tarball (~/.local/bin)"
      fi
    fi
    if [[ "${deb_ok}" -eq 0 ]]; then
      _rtk_install_tarball "${ver}" "${arch}" "${tmp}" \
        || _ensure_warn "RTK tarball install failed — continuing without rtk"
    fi
    rm -rf "${tmp}"
  fi

  if ! command -v rtk >/dev/null 2>&1 && [[ ! -x "${HOME}/.local/bin/rtk" ]]; then
    _ensure_warn "RTK install did not produce an rtk binary on PATH"
    return 0
  fi
  _ensure_info "RTK ready: $(rtk --version 2>/dev/null | head -1 || echo rtk)"
}

ensure_host_deps() {
  ensure_jq
  ensure_pipx
  ensure_node_optional
  ensure_rtk
}
