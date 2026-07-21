#!/usr/bin/env bash
# Create/refresh the AgentCore project virtualenv, install deps + editable CLI,
# and put `agentcore` on the user PATH (~/.local/bin).
#
# Override location with AGENTCORE_VENV_DIR (default: .venv). Isolated smoke uses
# .ac-venv to avoid Cursor sandbox read-only binds on paths named ".venv".
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

VENV_DIR="${AGENTCORE_VENV_DIR:-.venv}"
VENV_PATH="${ROOT}/${VENV_DIR}"

python3 -m venv "${VENV_PATH}" || true
"${VENV_PATH}/bin/python" -m pip install --upgrade pip
"${VENV_PATH}/bin/pip" install -r requirements-dev.txt
"${VENV_PATH}/bin/pip" install -e "${ROOT}"

echo "OK: ${VENV_PATH} ready"
"${VENV_PATH}/bin/python" -c "import fastapi,httpx,pytest,psycopg,agentcore_cli,usage_profile; print('imports ok')"

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
"${VENV_PATH}/bin/agentcore" "${PATH_ARGS[@]}"

echo
echo "Use: ${VENV_PATH}/bin/agentcore --help"
echo "Or:  source ${VENV_PATH}/bin/activate && agentcore --help"
