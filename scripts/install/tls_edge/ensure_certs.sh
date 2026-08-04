#!/usr/bin/env bash
# Ensure TLS cert/key exist; export AGENTCORE_TLS_CERT and AGENTCORE_TLS_KEY.
# Source after setting AGENTCORE_DATA_ROOT (and optional AGENTCORE_PUBLIC_HOSTNAME).
# shellcheck shell=bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTCORE_ROOT="${AGENTCORE_ROOT:-$(cd "${SCRIPT_DIR}/../../.." && pwd)}"
PY="${AGENTCORE_ROOT}/${AGENTCORE_VENV_DIR:-.venv}/bin/python"

if [[ ! -x "${PY}" ]]; then
  printf '%s FAIL  missing venv python at %s (run install stage 02)\n' "[tls_edge]" "${PY}" >&2
  exit 1
fi

: "${AGENTCORE_DATA_ROOT:?AGENTCORE_DATA_ROOT must be set}"
export AGENTCORE_PUBLIC_HOSTNAME="${AGENTCORE_PUBLIC_HOSTNAME:-localhost}"

eval "$(
  AGENTCORE_DATA_ROOT="${AGENTCORE_DATA_ROOT}" \
  AGENTCORE_PUBLIC_HOSTNAME="${AGENTCORE_PUBLIC_HOSTNAME}" \
  "${PY}" -c '
import os
from pathlib import Path
from agentcore_cli.tls_certs import ensure_tls_material

data_root = Path(os.environ["AGENTCORE_DATA_ROOT"])
hostname = os.environ.get("AGENTCORE_PUBLIC_HOSTNAME", "localhost")
material = ensure_tls_material(data_root=data_root, hostname=hostname)
print(f"export AGENTCORE_TLS_CERT={material.cert_path}")
print(f"export AGENTCORE_TLS_KEY={material.key_path}")
print(f"export AGENTCORE_TLS_GENERATED={1 if material.generated else 0}")
'
)"

printf '%s OK    hostname=%s cert=%s generated=%s\n' \
  "[tls_edge]" "${AGENTCORE_PUBLIC_HOSTNAME}" "${AGENTCORE_TLS_CERT}" "${AGENTCORE_TLS_GENERATED:-0}" >&2
