#!/usr/bin/env bash
# Wait until one or more Compose containers are healthy, then exit.
# Hard timeout: never spin forever (agents must cut off and report).
#
# Usage:
#   ./wait-healthy.sh [--timeout SEC] [--interval SEC] CONTAINER [CONTAINER...]
#
# Exit codes:
#   0  all containers healthy
#   1  timeout (still starting/unhealthy)
#   2  container missing, exited, or restarting loop
#   64 usage error

set -euo pipefail

TIMEOUT_SEC=90
INTERVAL_SEC=5
CONTAINERS=()

usage() {
  echo "Usage: $0 [--timeout SEC] [--interval SEC] CONTAINER [CONTAINER...]" >&2
  echo "Defaults: --timeout ${TIMEOUT_SEC} --interval ${INTERVAL_SEC}" >&2
  exit 64
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --timeout)
      [[ $# -ge 2 ]] || usage
      TIMEOUT_SEC="$2"
      shift 2
      ;;
    --interval)
      [[ $# -ge 2 ]] || usage
      INTERVAL_SEC="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    --)
      shift
      CONTAINERS+=("$@")
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage
      ;;
    *)
      CONTAINERS+=("$1")
      shift
      ;;
  esac
done

[[ ${#CONTAINERS[@]} -gt 0 ]] || usage

deadline=$((SECONDS + TIMEOUT_SEC))
# Restarting more than this many consecutive polls ⇒ treat as failure (not "still booting").
max_restarting_streak=6
declare -A restarting_streak=()

status_of() {
  local name="$1" out
  if ! out="$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$name" 2>/dev/null)"; then
    echo missing
    return 0
  fi
  out="${out//$'\r'/}"
  out="${out%%$'\n'*}"
  if [[ -z "$out" ]]; then
    echo missing
  else
    printf '%s\n' "$out"
  fi
}

all_healthy() {
  local name st
  for name in "${CONTAINERS[@]}"; do
    st="$(status_of "$name")"
    [[ "$st" == "healthy" ]] || return 1
  done
  return 0
}

while (( SECONDS < deadline )); do
  remaining=$((deadline - SECONDS))
  line="remaining=${remaining}s"
  failed=0

  for name in "${CONTAINERS[@]}"; do
    st="$(status_of "$name")"
    line+=" ${name}=${st}"

    case "$st" in
      healthy)
        restarting_streak["$name"]=0
        ;;
      missing|exited|dead)
        echo "$line" >&2
        echo "FAIL: ${name} is ${st} — aborting (not waiting full timeout)" >&2
        docker logs "$name" 2>&1 | tail -40 || true
        exit 2
        ;;
      restarting)
        restarting_streak["$name"]=$((${restarting_streak["$name"]:-0} + 1))
        if (( restarting_streak["$name"] >= max_restarting_streak )); then
          echo "$line" >&2
          echo "FAIL: ${name} restarting for ${restarting_streak[$name]} polls — aborting" >&2
          docker logs "$name" 2>&1 | tail -50 || true
          exit 2
        fi
        ;;
      *)
        restarting_streak["$name"]=0
        ;;
    esac
  done

  echo "$line"

  if all_healthy; then
    echo "OK: all healthy"
    exit 0
  fi

  # Sleep at most INTERVAL, but never past the deadline by more than a second.
  sleep_for=$INTERVAL_SEC
  if (( SECONDS + sleep_for > deadline )); then
    sleep_for=$((deadline - SECONDS))
    (( sleep_for > 0 )) || break
  fi
  sleep "$sleep_for"
done

echo "TIMEOUT: waited ${TIMEOUT_SEC}s; containers not healthy:" >&2
for name in "${CONTAINERS[@]}"; do
  echo "  ${name}=$(status_of "$name")" >&2
  docker logs "$name" 2>&1 | tail -30 || true
done
exit 1
