#!/usr/bin/env bash
# Push ai-toolstack to AgentCore host and run install-agentcore (rules + skills + MCP).
#
# Usage:
#   AGENTCORE_HOST=root@192.168.1.150 AGENTCORE_SSHPASS=... ./ai-toolstack/scripts/push-agentcore-stack.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${SCRIPT_DIR}/../lib/paths.sh"

HOST="${AGENTCORE_HOST:-root@192.168.1.150}"
REMOTE_ROOT="${AGENTCORE_ROOT:-/opt/AgentCore}"
SSHPASS="${AGENTCORE_SSHPASS:-}"

if [[ -z "${SSHPASS}" ]]; then
  echo "Set AGENTCORE_SSHPASS for non-interactive SSH" >&2
  exit 1
fi

export SSHPASS
SSH=(sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 "${HOST}")
SCP=(sshpass -e scp -o StrictHostKeyChecking=no)

info() { echo "[push-agentcore] $*"; }

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

info "Packaging ai-toolstack..."
tar -C "${AI_TOOLSTACK_ROOT}/.." \
  --exclude='ai-toolstack/data/local/node_modules' \
  --exclude='ai-toolstack/data/graphify-out' \
  --exclude='ai-toolstack/data/graphify' \
  --exclude='ai-toolstack/data/code-review-graph' \
  -czf "${TMP}/ai-toolstack.tgz" ai-toolstack

info "Upload to ${HOST}:${REMOTE_ROOT}..."
"${SCP[@]}" "${TMP}/ai-toolstack.tgz" "${HOST}:/tmp/ai-toolstack.tgz"

REMOTE_SCRIPT=$(cat <<EOF
set -e
rm -rf ${REMOTE_ROOT}/ai-toolstack
tar -xzf /tmp/ai-toolstack.tgz -C ${REMOTE_ROOT}
rm -f /tmp/ai-toolstack.tgz
cd ${REMOTE_ROOT}
chmod +x ai-toolstack/scripts/*.sh ai-toolstack/install.sh
export PATH="\${HOME}/.local/bin:\${PATH}"
./ai-toolstack/scripts/install-agentcore.sh
EOF
)

info "Running install-agentcore on remote..."
"${SSH[@]}" "${REMOTE_SCRIPT}"

info "Done. Cursor on ${HOST}: Reload Window; workspace ${REMOTE_ROOT}"
