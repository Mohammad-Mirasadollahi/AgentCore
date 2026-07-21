# ai-toolstack-sync — single-instance lock (optional for --background).

sync_acquire_lock() {
  if [[ "${BACKGROUND:-false}" == true ]]; then
    return 0
  fi
  if [[ -f "${LOCK_FILE}" ]]; then
    local pid
    pid="$(cat "${LOCK_FILE}" 2>/dev/null || true)"
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      sync_warn "sync already running (pid ${pid})"
      exit 1
    fi
    rm -f "${LOCK_FILE}"
  fi
  echo $$ > "${LOCK_FILE}"
  trap 'rm -f "${LOCK_FILE}"' EXIT
}
