# Guard: internal stage scripts — only callable from ai-toolstack.sh (default = graph refresh).
# shellcheck shell=bash
ai_toolstack_require_internal() {
  if [[ "${AI_TOOLSTACK_INTERNAL:-}" != "1" ]]; then
    local cli="${AI_TOOLSTACK_CLI:-./ai-toolstack/scripts/ai-toolstack.sh}"
    echo "Internal stage — use: ${cli} [options]" >&2
    echo "  Example: ${cli} --rebuild" >&2
    exit 1
  fi
}
