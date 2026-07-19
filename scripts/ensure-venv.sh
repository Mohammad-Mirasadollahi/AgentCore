#!/usr/bin/env bash
# Create/refresh the AgentCore project virtualenv, install deps + editable CLI,
# and put `agentcore` on the user PATH (~/.local/bin).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

python3 -m venv .venv || true
"${ROOT}/.venv/bin/python" -m pip install --upgrade pip
"${ROOT}/.venv/bin/pip" install -r requirements-dev.txt
"${ROOT}/.venv/bin/pip" install -e "${ROOT}"

echo "OK: ${ROOT}/.venv ready"
"${ROOT}/.venv/bin/python" -c "import fastapi,httpx,pytest,psycopg,agentcore_cli,usage_profile; print('imports ok')"

# Install CLI onto ~/.local/bin and optionally update shell rc for PATH.
SHELL_RC=""
if [[ -n "${AGENTCORE_SHELL_RC:-}" ]]; then
  SHELL_RC="${AGENTCORE_SHELL_RC}"
elif [[ "${SHELL:-}" == */zsh ]] && [[ -f "${HOME}/.zshrc" ]]; then
  SHELL_RC=".zshrc"
elif [[ -f "${HOME}/.bashrc" ]]; then
  SHELL_RC=".bashrc"
fi

PATH_ARGS=(path install)
if [[ -n "${SHELL_RC}" ]]; then
  PATH_ARGS+=(--shell-rc "${SHELL_RC}")
fi
"${ROOT}/.venv/bin/agentcore" "${PATH_ARGS[@]}"

echo
echo "Use: agentcore --help"
echo "Or:  source ${ROOT}/.venv/bin/activate && agentcore --help"
