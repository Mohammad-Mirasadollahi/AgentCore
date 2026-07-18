#!/usr/bin/env python3
"""CLI entry for Phase 6 CheckPhaseGate."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUPPORT = ROOT / "tests" / "support"
sys.path.insert(0, str(SUPPORT))

from phase6.gate import check_phase_gate  # noqa: E402
from phase6.runtime_scenario import run_runtime_scenario  # noqa: E402
from phase6.checks import run_all_checks  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AgentCore Phase 6 verification gate")
    parser.add_argument("--run-suites", action="store_true", help="Also execute Phase 1-5 pytest suites")
    parser.add_argument("--waiver-ref", default=None, help="Optional waiver issue/decision ref")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report")
    args = parser.parse_args()

    if args.run_suites:
        os.environ["AGENTCORE_PHASE6_RUN_SUITES"] = "1"

    decision = check_phase_gate(run_suites=args.run_suites, waiver_ref=args.waiver_ref)
    checks = run_all_checks()
    runtime = run_runtime_scenario()
    report = {
        "gate": decision.public(),
        "checks": [item.public() for item in checks],
        "runtime_scenario": runtime.public(),
    }
    failed_checks = [item for item in checks if item.status != "passed"]
    runtime_failed = runtime.status != "passed"
    gate = decision.public()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Phase 6 gate: {gate['status']} ({gate['passed_count']} passed, {gate['failed_count']} failed)")
        print(f"Verification checks: {sum(1 for item in checks if item.status == 'passed')}/{len(checks)} passed")
        print(f"Runtime scenario: {runtime.status}")
        for item in decision.checks:
            if item.status == "failed":
                print(f"  FAIL {item.check_id}: {item.message}")
        for item in failed_checks:
            print(f"  FAIL {item.check_id}: {item.message}")

    if decision.status == "fail" or failed_checks or runtime_failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
