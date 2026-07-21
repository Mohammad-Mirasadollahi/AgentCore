#!/usr/bin/env bash
# Sync custom Cursor rules/skills into ai-toolstack/cursor-agent-backup/ (git-tracked archive).
# Idempotent: copies only when canonical sources differ from the archive.
#
# Usage:
#   ./ai-toolstack/scripts/sync-cursor-agent-backup.sh           # sync if stale
#   ./ai-toolstack/scripts/sync-cursor-agent-backup.sh --check # exit 2 if stale, 0 if up to date
#   ./ai-toolstack/scripts/sync-cursor-agent-backup.sh --force   # always sync
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${REPO_ROOT}/ai-toolstack/cursor-agent-backup"
CHECK_ONLY=0
FORCE=0

info() { echo "INFO: cursor-agent-backup: $*"; }
ok() { echo "OK: cursor-agent-backup: $*"; }

usage() {
  cat <<EOF
Sync project/global Cursor rules and skills into ai-toolstack/cursor-agent-backup/.

Usage:
  $0 [--check] [--force]

  --check   Exit 0 when archive matches sources; exit 2 when sync is needed.
  --force   Always copy (skip change detection).
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) CHECK_ONLY=1 ;;
    --force) FORCE=1 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

# Return 0 when directory trees differ (sync needed).
tree_differs() {
  local src="$1" dest="$2"

  [[ -d "${src}" ]] || return 1
  mkdir -p "${dest}"
  [[ -d "${dest}" ]] || return 0

  if diff -qr "${src}" "${dest}" >/dev/null 2>&1; then
    return 1
  fi
  return 0
}

# Return 0 when any glob source file differs from dest (sync needed).
files_differ() {
  local dest_dir="$1"
  shift
  local src pattern base

  mkdir -p "${dest_dir}"

  for pattern in "$@"; do
    for src in ${pattern}; do
      [[ -e "${src}" ]] || continue
      base="$(basename "${src}")"
      if [[ ! -f "${dest_dir}/${base}" ]] || ! cmp -s "${src}" "${dest_dir}/${base}"; then
        return 0
      fi
    done
  done

  # Extra files in dest that are not in source glob.
  local existing
  for existing in "${dest_dir}"/*; do
    [[ -e "${existing}" ]] || continue
    base="$(basename "${existing}")"
    local found=0
    for pattern in "$@"; do
      for src in ${pattern}; do
        [[ "$(basename "${src}")" == "${base}" ]] && found=1 && break
      done
      (( found )) && break
    done
    if (( ! found )); then
      return 0
    fi
  done

  return 1
}

global_slot_differs() {
  local src="$1" dest="$2"
  local -a entries=()

  if [[ -d "${src}" ]] && compgen -G "${src}/*" >/dev/null; then
    tree_differs "${src}" "${dest}"
    return $?
  fi

  mkdir -p "${dest}"
  mapfile -t entries < <(find "${dest}" -mindepth 1 -maxdepth 1 ! -name '.gitkeep' 2>/dev/null || true)
  ((${#entries[@]} > 0))
}

needs_sync() {
  files_differ "${DEST}/rules/project" "${REPO_ROOT}/ai-toolstack/rules/*.mdc" && return 0
  tree_differs "${REPO_ROOT}/ai-toolstack/skills/thinkingsoc" "${DEST}/skills/project" && return 0
  files_differ "${DEST}/entrypoints" \
    "${REPO_ROOT}/AGENTS.md" \
    "${REPO_ROOT}/.cursorrules" && return 0
  tree_differs "${REPO_ROOT}/docs/agents" "${DEST}/agents" && return 0
  global_slot_differs "${HOME}/.cursor/rules" "${DEST}/rules/global" && return 0
  global_slot_differs "${HOME}/.cursor/skills" "${DEST}/skills/global" && return 0
  return 1
}

run_sync() {
  mkdir -p \
    "${DEST}/rules/project" \
    "${DEST}/rules/global" \
    "${DEST}/skills/project" \
    "${DEST}/skills/global" \
    "${DEST}/entrypoints" \
    "${DEST}/agents"

  rm -rf "${DEST}/rules/project"
  mkdir -p "${DEST}/rules/project"
  cp -f "${REPO_ROOT}"/ai-toolstack/rules/*.mdc "${DEST}/rules/project/"
  rm -rf "${DEST}/skills/project"
  mkdir -p "${DEST}/skills/project"
  cp -a "${REPO_ROOT}/ai-toolstack/skills/thinkingsoc/." "${DEST}/skills/project/"
  cp -f "${REPO_ROOT}/AGENTS.md" "${REPO_ROOT}/.cursorrules" "${DEST}/entrypoints/"
  cp -f "${REPO_ROOT}"/docs/agents/*.md "${DEST}/agents/"

  if [[ -d "${HOME}/.cursor/rules" ]] && compgen -G "${HOME}/.cursor/rules/*" >/dev/null; then
    rm -rf "${DEST}/rules/global"
    mkdir -p "${DEST}/rules/global"
    cp -a "${HOME}/.cursor/rules/." "${DEST}/rules/global/"
  else
    rm -rf "${DEST}/rules/global"
    mkdir -p "${DEST}/rules/global"
    : >"${DEST}/rules/global/.gitkeep"
  fi

  if [[ -d "${HOME}/.cursor/skills" ]] && compgen -G "${HOME}/.cursor/skills/*" >/dev/null; then
    rm -rf "${DEST}/skills/global"
    mkdir -p "${DEST}/skills/global"
    cp -a "${HOME}/.cursor/skills/." "${DEST}/skills/global/"
  else
    rm -rf "${DEST}/skills/global"
    mkdir -p "${DEST}/skills/global"
    : >"${DEST}/skills/global/.gitkeep"
  fi
}

if (( CHECK_ONLY )); then
  if (( FORCE )) || needs_sync; then
    exit 2
  fi
  exit 0
fi

if (( FORCE )) || needs_sync; then
  info "sources changed — refreshing archive"
  run_sync
  ok "archive refreshed ($(find "${DEST}" -type f | wc -l | tr -d ' ') files)"
  exit 0
fi

ok "up to date (no rule/skill changes)"
exit 0
