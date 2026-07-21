#!/usr/bin/env bash
# Thin wrapper — all work is done by install.sh.
# Kept for backwards compatibility and doc links.
#
# Usage:
#   ./ai-toolstack/scripts/restore-cursor-agent-config.sh
#   ./ai-toolstack/scripts/restore-cursor-agent-config.sh --full   # same as install.sh (default verify)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${SCRIPT_DIR}/../lib/paths.sh"

FULL=false
for arg in "$@"; do
  case "${arg}" in
    --full) FULL=true ;;
  esac
done

echo "[restore-cursor-agent] Delegating to ./ai-toolstack/install.sh (rules + skills + manifest)"
if [[ "${FULL}" == true ]]; then
  exec "${AI_TOOLSTACK_ROOT}/install.sh"
else
  exec "${AI_TOOLSTACK_ROOT}/install.sh" --no-verify
fi
