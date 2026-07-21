#!/usr/bin/env bash
# Pre-commit / CI: fail if summary index files are stale vs their source docs.
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${_SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"
python3 "${REPO_ROOT}/ai-toolstack/scripts/stamp-summary-hashes.py" --check
