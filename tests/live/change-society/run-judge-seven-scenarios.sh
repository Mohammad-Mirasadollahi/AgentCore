#!/usr/bin/env bash
# Canonical judge bundle: seven domains, LangGraph workers + AgentCore governance.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/run-langgraph-sdk-live-seven-scenarios.sh" "$@"
