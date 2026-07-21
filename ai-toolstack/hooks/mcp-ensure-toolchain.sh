#!/usr/bin/env bash
# Cursor sessionStart: ensure node/npx for MCP and refresh mcp-lazy cache when stale.
set -euo pipefail

# shellcheck source=../lib/paths.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/paths.sh"
# shellcheck source=../lib/resolve-node.sh
source "${AI_TOOLSTACK_ROOT}/lib/resolve-node.sh"

message="MCP toolchain OK"
passed=true

if ! ensure_node_toolchain; then
  message="MCP toolchain: node/npx not found — run ./ai-toolstack/install.sh"
  passed=false
else
  cache="${HOME}/.mcp-lazy/tool-cache.json"
  servers="${HOME}/.mcp-lazy/servers.json"
  if [[ ! -f "${cache}" ]] || { [[ -f "${servers}" ]] && [[ "${servers}" -nt "${cache}" ]]; }; then
    export PATH="${NODE_TOOLCHAIN_BIN}:${PATH}"
    local_mcp="${AI_TOOLSTACK_LOCAL}/node_modules/.bin/mcp-lazy"
    if [[ -x "${local_mcp}" ]]; then
      mcp_init_cmd=("${local_mcp}" "init")
    else
      mcp_init_cmd=("${NODE_TOOLCHAIN_BIN}/npx" "-y" "mcp-lazy" "init")
    fi
    if timeout 120 env MCP_LAZY_VERBOSE=0 MCP_LAZY_DEBUG=0 \
      "${mcp_init_cmd[@]}" >/dev/null 2>&1; then
      message="MCP toolchain OK (refreshed mcp-lazy cache)"
    else
      message="MCP toolchain OK but mcp-lazy init failed — run ./ai-toolstack/install.sh"
      passed=false
    fi
  fi
fi

python3 -c 'import json,sys; print(json.dumps({"message": sys.argv[1], "passed": sys.argv[2] == "true"}))' \
  "${message}" "${passed}" 2>/dev/null \
  || echo '{"passed":true}'
exit 0
