#!/usr/bin/env bash
# AgentCore: install ai-toolstack at /opt/AgentCore (Ponytail + mcp-lazy; no ThinkingSOC-only rules).
#
# Usage (on AgentCore host as root):
#   /opt/AgentCore/ai-toolstack/scripts/install-agentcore.sh
#   /opt/AgentCore/ai-toolstack/scripts/install-agentcore.sh --no-verify
#
# Wires: .cursor/rules, .cursor/skills, .agents/skills (mirror), AGENTS.md, .cursorrules, docs/agents/
# From ThinkingSOC dev host: AGENTCORE_SSHPASS=... ./ai-toolstack/scripts/push-agentcore-stack.sh
#
set -euo pipefail

AGENTCORE_ROOT="${AGENTCORE_ROOT:-/opt/AgentCore}"
export AI_TOOLSTACK_PROFILE=agentcore
export REPO_ROOT="${AGENTCORE_ROOT}"
export PATH="${HOME}/.local/bin:${PATH}"

cd "${REPO_ROOT}"
INSTALL="${REPO_ROOT}/ai-toolstack/install.sh"
if [[ ! -f "${INSTALL}" ]]; then
  echo "install-agentcore: missing ${INSTALL}" >&2
  exit 1
fi
chmod +x "${INSTALL}" "${REPO_ROOT}/ai-toolstack/scripts/"*.sh 2>/dev/null || true
exec "${INSTALL}" "$@"
