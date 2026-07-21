#!/usr/bin/env bash
# ThinkingSOC ai-toolstack — unified CLI (default: graph refresh; also stats, benchmark, verify, timer).
# Usage: ./ai-toolstack/scripts/ai-toolstack.sh help
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${_SCRIPT_DIR}/../lib/paths.sh"

export PYTHONPATH="${AI_TOOLSTACK_ROOT}/lib${PYTHONPATH:+:${PYTHONPATH}}"
export AI_TOOLSTACK_CLI="${_SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}")"
export REPO_ROOT

exec python3 -m cli.ai_toolstack "$@"
