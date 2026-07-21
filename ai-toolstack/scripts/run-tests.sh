#!/usr/bin/env bash
# Run ai-toolstack unit tests + CLI smoke checks.
# Usage: ./ai-toolstack/scripts/run-tests.sh [--quick]
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

QUICK=false
[[ "${1:-}" == "--quick" ]] && QUICK=true

AI_CLI="${REPO_ROOT}/ai-toolstack/scripts/ai-toolstack.sh"
export PYTHONPATH="${REPO_ROOT}/ai-toolstack/lib${PYTHONPATH:+:${PYTHONPATH}}"

failures=0
pass() { echo "  OK   $*"; }
fail() { echo "  FAIL $*"; failures=$((failures + 1)); }

echo "=== token_stats unit tests ==="
if PYTHONPATH="${REPO_ROOT}/ai-toolstack/lib" python3 -m unittest token_stats.test_report -q; then
  pass "token_stats.test_report"
else
  fail "token_stats.test_report"
fi

echo ""
echo "=== stack config (MCP templates) ==="
if PYTHONPATH="${REPO_ROOT}/ai-toolstack/lib" python3 -m unittest discover -s ai-toolstack/tests -p 'test_*.py' -q; then
  pass "test_stack_config"
else
  fail "test_stack_config"
fi

echo ""
echo "=== CLI smoke ==="
"${AI_CLI}" help >/dev/null && pass "ai-toolstack.sh help" || fail "ai-toolstack.sh help"

if "${AI_CLI}" --check 2>&1 | tail -5 | grep -q 'Check only — no stages executed'; then
  pass "ai-toolstack.sh --check"
else
  fail "ai-toolstack.sh --check"
fi

"${AI_CLI}" stats status --since 24h >/dev/null && pass "ai-toolstack.sh stats status" || fail "stats status"
"${AI_CLI}" stats gain --since 24h >/dev/null && pass "ai-toolstack.sh stats gain" || fail "stats gain"
"${AI_CLI}" timer status >/dev/null && pass "ai-toolstack.sh timer status" || fail "timer status"

echo ""
echo "=== verify-install / verify ==="
if "${REPO_ROOT}/ai-toolstack/scripts/verify-install.sh" --quick; then
  pass "verify-install.sh --quick"
else
  fail "verify-install.sh --quick"
fi

if "${AI_CLI}" verify --quick; then
  pass "ai-toolstack.sh verify --quick"
else
  fail "ai-toolstack.sh verify --quick"
fi

echo ""
echo "=== frontend access-token session guard ==="
if (cd "${REPO_ROOT}/frontend" && node scripts/verify-access-token-session.mjs --run-tests); then
  pass "verify-access-token-session.mjs"
else
  fail "verify-access-token-session.mjs"
fi

if [[ "${QUICK}" == true ]]; then
  echo ""
  echo "=== Summary (--quick) ==="
  if [[ "${failures}" -eq 0 ]]; then
    echo "All quick tests PASSED."
    exit 0
  fi
  echo "FAILED: ${failures} check(s)"
  exit 1
fi

echo ""
echo "=== benchmark (all) ==="
"${AI_CLI}" benchmark all >/dev/null && pass "benchmark all" || fail "benchmark all"

echo ""
echo "=== Summary ==="
if [[ "${failures}" -eq 0 ]]; then
  echo "All tests PASSED."
  exit 0
fi
echo "FAILED: ${failures} check(s)"
exit 1
