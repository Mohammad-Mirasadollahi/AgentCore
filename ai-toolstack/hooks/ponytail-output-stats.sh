#!/usr/bin/env bash
# Cursor afterAgentResponse: log agent output brevity to token-stats JSONL.
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${_SCRIPT_DIR}/../lib/paths.sh"

export REPO_ROOT
export AI_TOOLSTACK_TOKEN_STATS_DIR="${TOKEN_STATS_DIR}"

PY="${AI_TOOLSTACK_SCRIPTS}/log-ponytail-output-stats.py"
if [[ ! -f "${PY}" ]] || ! command -v python3 >/dev/null 2>&1; then
  printf '{}\n'
  exit 0
fi

python3 "${PY}" || true
printf '{}\n'
exit 0
