#!/usr/bin/env bash
# Post-install verification for ThinkingSOC ai-toolstack.
#
# Usage:
#   ./ai-toolstack/scripts/verify-install.sh           # full verify
#   ./ai-toolstack/scripts/verify-install.sh --quick # symlinks + configs only (no mcp-lazy doctor)
#
set -euo pipefail

# shellcheck source=../lib/paths.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/paths.sh"

export REPO_ROOT PYTHONPATH="${AI_TOOLSTACK_ROOT}/lib${PYTHONPATH:+:${PYTHONPATH}}"
exec python3 "${AI_TOOLSTACK_ROOT}/lib/cli/verify_install.py" "$@"
