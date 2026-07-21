#!/usr/bin/env bash
# Internal sync entry — invoked only via: ./ai-toolstack/scripts/ai-toolstack.sh
set -euo pipefail

_SYNC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_AI_TOOLSTACK_ROOT="$(cd "${_SYNC_ROOT}/.." && pwd)"
_SYNC_LIB="${_SYNC_ROOT}/sync"
export SYNC_SCRIPT_PATH="${_AI_TOOLSTACK_ROOT}/scripts/ai-toolstack.sh"
export AI_TOOLSTACK_INTERNAL=1

# shellcheck source=../paths.sh
source "${_SYNC_ROOT}/paths.sh"
# shellcheck source=../log.sh
source "${_SYNC_ROOT}/log.sh"
# shellcheck source=config.sh
source "${_SYNC_LIB}/config.sh"
# shellcheck source=defaults.sh
source "${_SYNC_LIB}/defaults.sh"
# shellcheck source=logging.sh
source "${_SYNC_LIB}/logging.sh"
# shellcheck source=lock.sh
source "${_SYNC_LIB}/lock.sh"
# shellcheck source=args.sh
source "${_SYNC_LIB}/args.sh"
# shellcheck source=plan.sh
source "${_SYNC_LIB}/plan.sh"
# shellcheck source=run.sh
source "${_SYNC_LIB}/run.sh"

sync_parse_args "$@"
sync_validate_args
sync_main
