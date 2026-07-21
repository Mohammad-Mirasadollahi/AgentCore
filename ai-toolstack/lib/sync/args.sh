# ai-toolstack-sync — CLI parsing.

sync_parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --check|-n) CHECK_ONLY=true ;;
      --force|-f) FORCE=true ;;
      --rebuild|-R) REBUILD=true; FORCE=true ;;
      --background) BACKGROUND=true ;;
      --quiet|-q) QUIET=true ;;
      -h|--help)
        sed -n '2,20p' "${SYNC_SCRIPT_PATH}" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
      *)
        echo "FAIL: unknown option '$1' (run with --help)" >&2
        exit 1
        ;;
    esac
    shift
  done
}

sync_validate_args() {
  return 0
}
