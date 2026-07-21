#!/usr/bin/env bash
# Remove Graphify/CRG runtime paths and repo-root symlinks (stack removed 2026-07).
#
# Usage:
#   ./ai-toolstack/scripts/purge-legacy-graph-paths.sh           # delete data + symlinks
#   ./ai-toolstack/scripts/purge-legacy-graph-paths.sh --dry-run  # print only
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${SCRIPT_DIR}/../lib/paths.sh"

DRY=false
[[ "${1:-}" == "--dry-run" ]] && DRY=true

info() { echo "[purge-legacy-graph] $*"; }

remove_path() {
  local p="${1}"
  [[ -e "${p}" || -L "${p}" ]] || return 0
  if [[ "${DRY}" == true ]]; then
    info "would remove: ${p}"
    return 0
  fi
  rm -rf "${p}"
  info "removed: ${p}"
}

DATA="${AI_TOOLSTACK_DATA}"
REPO="${REPO_ROOT}"

info "Repo: ${REPO}"

# Repo-root symlinks / ignore files (legacy install.sh / CRG)
for link in \
  "${REPO}/graphify-out" \
  "${REPO}/.graphify" \
  "${REPO}/.code-review-graph" \
  "${REPO}/.code-review-graphignore"; do
  remove_path "${link}"
done

# Runtime artifacts under ai-toolstack/data/
for dir in \
  "${DATA}/graphify-out" \
  "${DATA}/graphify" \
  "${DATA}/code-review-graph"; do
  remove_path "${dir}"
done

# Stale empty/cache dirs left under ai-toolstack after Graphify MCP removal
for dir in \
  "${REPO}/ai-toolstack/graphify-out" \
  "${REPO}/ai-toolstack/lib/graphify-out" \
  "${REPO}/ai-toolstack/rules/graphify-out"; do
  remove_path "${dir}"
done

# Optional doc-tree caches (gitignored)
for dir in \
  "${REPO}/docs/graphify-out" \
  "${REPO}/backend/docs/graphify-out" \
  "${REPO}/frontend/docs/graphify-out" \
  "${REPO}/ai-toolstack/docs/graphify-out"; do
  remove_path "${dir}"
done

# Orphaned __pycache__ from deleted graphify/crg Python modules
if [[ "${DRY}" == true ]]; then
  while IFS= read -r -d '' f; do
    info "would remove: ${f}"
  done < <(find "${REPO}/ai-toolstack" -type f \( -path '*/__pycache__/*graphify*' -o -path '*/__pycache__/*crg*' \) -print0 2>/dev/null || true)
else
  find "${REPO}/ai-toolstack" -type f \( -path '*/__pycache__/*graphify*' -o -path '*/__pycache__/*crg*' \) -delete 2>/dev/null || true
  info "purged ai-toolstack __pycache__ graphify/crg artifacts (if any)"
fi

# Stale graphify bench logs in data/ (not other runtime)
if [[ "${DRY}" == true ]]; then
  shopt -s nullglob
  for f in "${DATA}"/graphify-* "${DATA}"/bench-backend-* "${DATA}"/bench-one.json "${DATA}"/ensure-out.json; do
    [[ -f "${f}" ]] && info "would remove: ${f}"
  done
  shopt -u nullglob
else
  shopt -s nullglob
  for f in "${DATA}"/graphify-* "${DATA}"/bench-backend-* "${DATA}"/bench-one.json "${DATA}"/ensure-out.json; do
    [[ -f "${f}" ]] && rm -f "${f}" && info "removed: ${f}"
  done
  shopt -u nullglob
fi

# Generated local leftovers (old watch/sync / bak servers with removed backends)
LOCAL="${AI_TOOLSTACK_LOCAL:-${DATA}/local}"
for f in \
  "${LOCAL}/crg-watch.toml" \
  "${LOCAL}/crg-update-last-line.txt" \
  "${LOCAL}/graphify-watch.service" \
  "${LOCAL}/mcp-lazy-servers.json.bak" \
  "${LOCAL}/sync-last-run.json"; do
  remove_path "${f}"
done

# Optional: uninstall pipx packages if present (host tools, not repo paths)
if command -v pipx >/dev/null 2>&1; then
  for pkg in code-review-graph graphifyy; do
    if pipx list 2>/dev/null | grep -qE "package[[:space:]]+${pkg}([[:space:]]|$)"; then
      if [[ "${DRY}" == true ]]; then
        info "would pipx uninstall: ${pkg}"
      else
        if pipx uninstall "${pkg}"; then
          info "pipx uninstalled: ${pkg}"
        else
          info "pipx uninstall skipped/failed: ${pkg}"
        fi
      fi
    fi
  done
fi

if [[ "${DRY}" == true ]]; then
  info "dry-run complete"
else
  info "done — re-run ./ai-toolstack/install.sh to refresh .cursor/skills symlinks"
fi
