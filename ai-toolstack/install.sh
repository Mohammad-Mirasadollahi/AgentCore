#!/usr/bin/env bash
# Wire ThinkingSOC ai-toolstack into Cursor, mcp-lazy, and repo-root symlinks.
#
# Also wires Cursor agent config from git-tracked canonical store:
#   ai-toolstack/rules/   → .cursor/rules/
#   ai-toolstack/skills/  → .cursor/skills/
#   cursor-agent-config/MANIFEST.md (regenerated each run)
#
# Implementation modules: ai-toolstack/lib/install/*.sh
#
# Usage:
#   ./ai-toolstack/install.sh              # full install + verify
#   ./ai-toolstack/install.sh --check      # show resolved paths only (no install)
#   ./ai-toolstack/install.sh --no-verify  # install without post-check
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/paths.sh
source "${SCRIPT_DIR}/lib/paths.sh"
# shellcheck source=lib/install/load.sh
source "${SCRIPT_DIR}/lib/install/load.sh"

CHECK_ONLY=false
NO_VERIFY=false
for arg in "$@"; do
  case "${arg}" in
    --check) CHECK_ONLY=true ;;
    --no-verify) NO_VERIFY=true ;;
  esac
done

if [[ "${CHECK_ONLY}" == true ]]; then
  install_print_check
  exit 0
fi

install_main "${NO_VERIFY}"
exit $?
