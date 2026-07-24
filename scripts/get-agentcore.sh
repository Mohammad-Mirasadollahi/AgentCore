#!/usr/bin/env bash
# AgentCore one-line bootstrap: fetch from GitHub, then run install.sh.
#
# Empty machine:
#   curl -fsSL https://raw.githubusercontent.com/Mohammad-Mirasadollahi/AgentCore/refs/heads/main/scripts/get-agentcore.sh | bash
# Prefer refs/heads/main over /main/ — GitHub raw CDN often serves a stale /main/ tip.
#
# Channels:
#   release — latest GitHub Release (immutable tag + source tarball)
#   main    — tip of the default branch (may be unreleased)
#
# Env overrides:
#   AGENTCORE_ROOT          Install directory (default /opt/AgentCore)
#   AGENTCORE_CHANNEL       release | main
#   AGENTCORE_GIT_HTTPS     Clone URL (default fixed public repo)
#   AGENTCORE_SKIP_INSTALL  1 = fetch only (tests / dry fetch)
#   AGENTCORE_CURL          curl binary (tests)
#   GITHUB_TOKEN            Optional; sent as Authorization for API/git over HTTPS
#
# shellcheck shell=bash
set -euo pipefail

AGENTCORE_REPO_SLUG="${AGENTCORE_REPO_SLUG:-Mohammad-Mirasadollahi/AgentCore}"
AGENTCORE_GIT_HTTPS="${AGENTCORE_GIT_HTTPS:-https://github.com/${AGENTCORE_REPO_SLUG}.git}"
AGENTCORE_GITHUB_API="${AGENTCORE_GITHUB_API:-https://api.github.com/repos/${AGENTCORE_REPO_SLUG}}"
AGENTCORE_CODELOAD="${AGENTCORE_CODELOAD:-https://codeload.github.com/${AGENTCORE_REPO_SLUG}}"
AGENTCORE_DEFAULT_ROOT="${AGENTCORE_DEFAULT_ROOT:-/opt/AgentCore}"
AGENTCORE_DEFAULT_BRANCH="${AGENTCORE_DEFAULT_BRANCH:-main}"

CURL_BIN="${AGENTCORE_CURL:-curl}"

log() { printf '[agentcore-get] %s\n' "$*" >&2; }
info() { log "INFO  $*"; }
ok() { log "OK    $*"; }
warn() { log "WARN  $*" >&2; }
fail() {
  log "FAIL  $*" >&2
  exit 1
}

have_cmd() { command -v "$1" >/dev/null 2>&1; }

require_cmds() {
  local missing=()
  local c
  for c in "$@"; do
    have_cmd "${c}" || missing+=("${c}")
  done
  if ((${#missing[@]})); then
    fail "missing required commands: ${missing[*]}"
  fi
}

curl_github() {
  local url="$1"
  shift
  local args=(-fsSL)
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    args+=(-H "Authorization: Bearer ${GITHUB_TOKEN}" -H "X-GitHub-Api-Version: 2022-11-28")
  fi
  args+=(-H "Accept: application/vnd.github+json")
  "${CURL_BIN}" "${args[@]}" "$@" "${url}"
}

# Like curl_github but does not fail on HTTP errors (caller checks body / exit).
curl_github_soft() {
  local url="$1"
  shift
  local args=(-sSL)
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    args+=(-H "Authorization: Bearer ${GITHUB_TOKEN}" -H "X-GitHub-Api-Version: 2022-11-28")
  fi
  args+=(-H "Accept: application/vnd.github+json")
  "${CURL_BIN}" "${args[@]}" "$@" "${url}" || true
}

parse_json_field() {
  local json="$1"
  local field="$2"
  if have_cmd python3; then
    printf '%s' "${json}" | python3 -c "import json,sys
raw=sys.stdin.read().strip()
if not raw:
  raise SystemExit(0)
data=json.loads(raw)
if isinstance(data, dict):
  print(data.get('${field}') or '')
elif isinstance(data, list) and data and isinstance(data[0], dict):
  print(data[0].get('${field}') or '')
"
  else
    printf '%s' "${json}" | sed -n "s/.*\"${field}\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" | head -n1
  fi
}

latest_release_tag() {
  local json tag
  json="$(curl_github_soft "${AGENTCORE_GITHUB_API}/releases/latest")"
  tag="$(parse_json_field "${json}" tag_name)"
  if [[ -n "${tag}" ]]; then
    printf '%s\n' "${tag}"
    return 0
  fi
  warn "No GitHub Release found; falling back to newest git tag"
  json="$(curl_github_soft "${AGENTCORE_GITHUB_API}/tags?per_page=1")"
  tag="$(parse_json_field "${json}" name)"
  if [[ -n "${tag}" ]]; then
    printf '%s\n' "${tag}"
    return 0
  fi
  return 1
}

normalize_channel() {
  local raw="${1:-}"
  case "${raw}" in
    release | stable | latest-release) printf '%s\n' release ;;
    main | edge | tip | latest) printf '%s\n' main ;;
    *) return 1 ;;
  esac
}

# curl|bash leaves stdin as the script pipe (not a TTY). Prompt via /dev/tty instead.
can_prompt() {
  if [[ "${AGENTCORE_NONINTERACTIVE:-0}" == "1" ]]; then
    return 1
  fi
  if [[ -t 0 ]]; then
    return 0
  fi
  # Path may exist while open fails (non-interactive CI / no controlling terminal).
  if { true <>/dev/tty; } 2>/dev/null; then
    return 0
  fi
  return 1
}

# Read one line from the operator (stdin TTY, or /dev/tty when piped).
read_prompt() {
  local prompt="$1"
  local ans=""
  if [[ -t 0 ]]; then
    read -r -p "${prompt}" ans || true
  elif { true <>/dev/tty; } 2>/dev/null; then
    # Prompt on the real terminal; do not consume the curl|bash script pipe.
    printf '%s' "${prompt}" >/dev/tty 2>/dev/null || true
    read -r ans </dev/tty 2>/dev/null || true
    printf '\n' >/dev/tty 2>/dev/null || true
  else
    fail "cannot prompt (no TTY); pass --channel release|main and optional --root"
  fi
  printf '%s\n' "${ans}"
}

prompt_channel() {
  if [[ -n "${AGENTCORE_CHANNEL:-}" ]]; then
    normalize_channel "${AGENTCORE_CHANNEL}" || fail "invalid AGENTCORE_CHANNEL=${AGENTCORE_CHANNEL} (use release|main)"
    return 0
  fi
  if ! can_prompt; then
    fail "non-interactive: pass --channel release|main (or AGENTCORE_CHANNEL)"
  fi
  echo >&2
  echo "Fetch channel:" >&2
  echo "  1) release  — latest GitHub Release (or newest tag if none)" >&2
  echo "  2) main     — latest commits on ${AGENTCORE_DEFAULT_BRANCH} (may be unreleased)" >&2
  local ans=""
  ans="$(read_prompt "Choose [1/2] (default 1): ")"
  case "${ans}" in
    "" | 1 | release | r | R) printf '%s\n' release ;;
    2 | main | m | M) printf '%s\n' main ;;
    *)
      normalize_channel "${ans}" || fail "invalid channel choice: ${ans}"
      ;;
  esac
}

prompt_root() {
  local root="${AGENTCORE_ROOT:-${AGENTCORE_DEFAULT_ROOT}}"
  if [[ -n "${AGENTCORE_ROOT:-}" ]]; then
    printf '%s\n' "${root}"
    return 0
  fi
  if ! can_prompt; then
    printf '%s\n' "${root}"
    return 0
  fi
  local ans=""
  ans="$(read_prompt "Install root [${root}]: ")"
  if [[ -n "${ans}" ]]; then
    root="${ans}"
  fi
  printf '%s\n' "${root}"
}

is_agentcore_git_checkout() {
  local root="$1"
  [[ -d "${root}/.git" ]] || return 1
  local url
  url="$(git -C "${root}" remote get-url origin 2>/dev/null || true)"
  [[ -n "${url}" ]] || return 1
  case "${url}" in
    *"${AGENTCORE_REPO_SLUG}"* | *"${AGENTCORE_REPO_SLUG%.git}"*) return 0 ;;
    *) return 1 ;;
  esac
}

preserve_paths() {
  cat <<'EOF'
.agentcore
.env
.venv
agentcore.sync.yaml
backend/deployments/compose/.env.local
EOF
}

sync_tree_preserving() {
  local staging="$1"
  local root="$2"
  mkdir -p "${root}"

  if have_cmd rsync; then
    local excludes=()
    local p
    while IFS= read -r p; do
      [[ -n "${p}" ]] || continue
      excludes+=(--exclude "${p}")
    done < <(preserve_paths)
    rsync -a --delete "${excludes[@]}" "${staging}/" "${root}/"
    return 0
  fi

  # Fallback without rsync: copy staging over root while skipping preserve paths.
  local tmp_keep
  tmp_keep="$(mktemp -d)"
  while IFS= read -r p; do
    [[ -n "${p}" ]] || continue
    if [[ -e "${root}/${p}" ]]; then
      mkdir -p "${tmp_keep}/$(dirname "${p}")"
      mv "${root}/${p}" "${tmp_keep}/${p}"
    fi
  done < <(preserve_paths)

  # Wipe root contents then move staging in.
  find "${root}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  # shellcheck disable=SC2045
  for item in "${staging}"/* "${staging}"/.[!.]* "${staging}"/..?*; do
    [[ -e "${item}" ]] || continue
    mv "${item}" "${root}/"
  done

  while IFS= read -r p; do
    [[ -n "${p}" ]] || continue
    if [[ -e "${tmp_keep}/${p}" ]]; then
      mkdir -p "${root}/$(dirname "${p}")"
      rm -rf "${root}/${p}"
      mv "${tmp_keep}/${p}" "${root}/${p}"
    fi
  done < <(preserve_paths)
  rm -rf "${tmp_keep}"
}

fetch_release_into() {
  local root="$1"
  local tag tarball staging
  require_cmds "${CURL_BIN}" tar mktemp
  if ! tag="$(latest_release_tag)"; then
    warn "No GitHub Release/tag on ${AGENTCORE_REPO_SLUG}; using channel main instead"
    fetch_main_into "${root}"
    return 0
  fi
  info "Latest release tag: ${tag}"
  tarball="$(mktemp /tmp/agentcore-release.XXXXXX)"
  staging="$(mktemp -d /tmp/agentcore-stage.XXXXXX)"
  cleanup_release() {
    rm -rf "${staging}" "${tarball}"
  }
  trap cleanup_release EXIT

  info "Downloading source tarball for ${tag}"
  curl_github "${AGENTCORE_CODELOAD}/tar.gz/refs/tags/${tag}" -o "${tarball}"
  tar -xzf "${tarball}" -C "${staging}" --strip-components=1
  [[ -f "${staging}/install.sh" ]] || fail "tarball missing install.sh (bad extract?)"
  sync_tree_preserving "${staging}" "${root}"
  mkdir -p "${root}/.agentcore"
  printf '%s\n' "${tag}" >"${root}/.agentcore/fetched-release-tag"
  ok "Tree updated from release ${tag} → ${root}"
  trap - EXIT
  cleanup_release
}

fetch_main_into() {
  local root="$1"
  require_cmds git
  if is_agentcore_git_checkout "${root}"; then
    info "Updating existing git checkout at ${root}"
    git -C "${root}" fetch --tags origin
    git -C "${root}" checkout "${AGENTCORE_DEFAULT_BRANCH}"
    git -C "${root}" pull --ff-only origin "${AGENTCORE_DEFAULT_BRANCH}"
    ok "Pulled ${AGENTCORE_DEFAULT_BRANCH} → ${root}"
    return 0
  fi

  if [[ -e "${root}" ]] && [[ -n "$(ls -A "${root}" 2>/dev/null || true)" ]]; then
    local staging
    staging="$(mktemp -d /tmp/agentcore-clone.XXXXXX)"
    cleanup_clone() {
      rm -rf "${staging}"
    }
    trap cleanup_clone EXIT
    info "Cloning ${AGENTCORE_DEFAULT_BRANCH} into staging (preserving local state under ${root})"
    git clone --branch "${AGENTCORE_DEFAULT_BRANCH}" --depth 1 "${AGENTCORE_GIT_HTTPS}" "${staging}/repo"
    sync_tree_preserving "${staging}/repo" "${root}"
    ok "Synced ${AGENTCORE_DEFAULT_BRANCH} → ${root}"
    trap - EXIT
    cleanup_clone
    return 0
  fi

  mkdir -p "$(dirname "${root}")"
  info "Cloning ${AGENTCORE_GIT_HTTPS} (${AGENTCORE_DEFAULT_BRANCH}) → ${root}"
  git clone --branch "${AGENTCORE_DEFAULT_BRANCH}" --depth 1 "${AGENTCORE_GIT_HTTPS}" "${root}"
  ok "Cloned → ${root}"
}

run_install() {
  local root="$1"
  shift
  [[ -f "${root}/install.sh" ]] || fail "missing ${root}/install.sh after fetch"
  if [[ "${AGENTCORE_SKIP_INSTALL:-0}" == "1" ]]; then
    info "AGENTCORE_SKIP_INSTALL=1 — not running install.sh"
    return 0
  fi

  local args=()
  local has_yes=0
  local has_noninteractive=0
  local has_role=0
  local a
  for a in "$@"; do
    case "${a}" in
      --yes | -y) has_yes=1 ;;
      --non-interactive) has_noninteractive=1 ;;
      --role) has_role=1 ;;
    esac
    args+=("${a}")
  done
  # CLI --role means agent/CI: no menus. Also skip "type yes" (unattended).
  if [[ "${has_role}" == "1" && "${has_noninteractive}" != "1" ]]; then
    args=(--non-interactive "${args[@]}")
    has_noninteractive=1
  fi
  if [[ "${has_noninteractive}" == "1" && "${has_yes}" != "1" ]]; then
    args=(--yes "${args[@]}")
  fi

  info "Running: bash install.sh ${args[*]}"
  (cd "${root}" && bash install.sh "${args[@]}")
}

usage() {
  cat <<EOF
AgentCore get/bootstrap — fetch from GitHub then run install.sh

Usage:
  curl -fsSL https://raw.githubusercontent.com/${AGENTCORE_REPO_SLUG}/refs/heads/main/scripts/get-agentcore.sh | bash
  bash scripts/get-agentcore.sh [get-options] [-- install.sh options...]

Get options:
  --channel release|main   Fetch channel (prompted on TTY if omitted)
  --root PATH              Install directory (default ${AGENTCORE_DEFAULT_ROOT})
  --yes, -y                Skip install.sh "type yes" (also implied by --non-interactive / --role)
  --skip-install           Fetch only (do not run install.sh)
  -h, --help               Show this help

Any other flags are passed through to install.sh (--role, --runtime, --upgrade, …).
Passing --role enables --non-interactive and --yes (unattended). Interactive runs still ask
install/upgrade, type yes, then client/server (and server MCP mode).

Channels:
  release  Latest GitHub Release tag (immutable); recommended for servers
  main     Tip of ${AGENTCORE_DEFAULT_BRANCH} (may be unreleased)
EOF
}

parse_and_run() {
  local channel=""
  local root=""
  local assume_yes=0
  local skip_install=0
  local install_args=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h | --help)
        usage
        exit 0
        ;;
      --channel)
        [[ $# -ge 2 ]] || fail "--channel needs release|main"
        channel="$(normalize_channel "$2")" || fail "invalid --channel $2"
        shift 2
        ;;
      --root)
        [[ $# -ge 2 ]] || fail "--root needs a path"
        root="$2"
        shift 2
        ;;
      --yes | -y)
        assume_yes=1
        install_args+=(--yes)
        shift
        ;;
      --skip-install)
        skip_install=1
        shift
        ;;
      --)
        shift
        install_args+=("$@")
        break
        ;;
      *)
        install_args+=("$1")
        shift
        ;;
    esac
  done

  if [[ -n "${channel}" ]]; then
    AGENTCORE_CHANNEL="${channel}"
  fi
  if [[ -n "${root}" ]]; then
    AGENTCORE_ROOT="${root}"
  fi
  if [[ "${skip_install}" == "1" ]]; then
    AGENTCORE_SKIP_INSTALL=1
  fi
  if [[ "${assume_yes}" == "1" ]]; then
    export INSTALL_ASSUME_YES=1
  else
    # Do not inherit a stale INSTALL_ASSUME_YES from the operator environment.
    unset INSTALL_ASSUME_YES || true
  fi

  channel="$(prompt_channel)"
  root="$(prompt_root)"
  root="$(cd / && readlink -f "${root}" 2>/dev/null || python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "${root}")"

  info "Channel=${channel}  root=${root}"
  mkdir -p "${root}"

  case "${channel}" in
    release) fetch_release_into "${root}" ;;
    main) fetch_main_into "${root}" ;;
    *) fail "internal: bad channel ${channel}" ;;
  esac

  run_install "${root}" "${install_args[@]+"${install_args[@]}"}"
}

# Allow unit tests to source helpers without executing main.
if [[ "${GET_AGENTCORE_LIB_ONLY:-0}" == "1" ]]; then
  return 0 2>/dev/null || exit 0
fi

parse_and_run "$@"
