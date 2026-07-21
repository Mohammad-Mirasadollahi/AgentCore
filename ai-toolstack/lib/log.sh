# Shared timestamped console logging for ai-toolstack shell scripts.
# Usage: source "$(dirname ...)/lib/log.sh"
#
# Timestamps default to the **system local timezone** (/etc/localtime).
# No TZ env var is required. Override only when needed: TZ=UTC ./script.sh

# System local timezone, ISO 8601 with offset (e.g. 2026-06-18T10:31:27+03:30)
ts_now() { date -Iseconds; }

# Print one line with timezone-aware ISO timestamp prefix.
ts_log() { echo "[$(ts_now)] $*"; }

# Section header (blank line + timestamped title).
ts_section() {
  echo ""
  ts_log "=== $* ==="
}

# Indented line with timestamp.
ts_item() { ts_log "  $*"; }

# Same as ts_item but stderr — safe while stdout is piped (bash defers background stdout).
ts_item_stderr() { ts_log "  $*" >&2; }

# Pipe child stdout/stderr — one timestamped line per input line.
ts_pipe_lines() {
  while IFS= read -r line || [[ -n "${line}" ]]; do
    ts_item "${line}"
  done
}
