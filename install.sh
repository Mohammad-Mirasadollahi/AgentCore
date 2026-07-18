#!/usr/bin/env bash
# One-command Change Society install from repository root.
# Usage: bash install.sh   (or: bash install.sh --profile verify)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$ROOT/hackathon/install.sh" "$@"
