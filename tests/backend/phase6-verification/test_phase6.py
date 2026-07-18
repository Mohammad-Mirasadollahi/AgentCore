import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUPPORT = ROOT / "tests" / "support"
if str(SUPPORT) not in sys.path:
    sys.path.insert(0, str(SUPPORT))

from phase6.catalog import PHASE_SLICES, canonical_test_command, required_checks_for_phase
from phase6.checks import run_all_checks
from phase6.gate import check_phase_gate, explain_failed_check
from phase6.runtime_scenario import run_runtime_scenario


def test_catalog_covers_phases_one_through_five():
    assert [item.phase for item in PHASE_SLICES] == [1, 2, 3, 4, 5]
    checks = required_checks_for_phase(1)
    assert checks[0]["command"] == canonical_test_command(1)
    assert "core-data-service" in checks[0]["subject_ref"]


def test_phase_gate_passes_path_and_readme_checks():
    decision = check_phase_gate(run_suites=False)
    report = decision.public()
    assert decision.status == "pass"
    assert report["blocked"] is False
    assert report["passed_count"] >= 15
    assert report["failed_count"] == 0


def test_verification_checks_contracts_state_idempotency_redaction():
    results = run_all_checks()
    assert results
    assert all(item.status == "passed" for item in results)
    types = {item.check_type for item in results}
    assert {
        "contract",
        "state_machine",
        "idempotency",
        "redaction",
        "retrieval",
        "docs_drift",
        "rule_evaluation",
        "broker_delivery",
        "catalog_coverage",
    } <= types
    subjects = {item.subject_ref for item in results if item.check_type == "broker_delivery"}
    assert "adapter-service" in subjects


def test_runtime_scenario_stitches_phases_with_shared_correlation():
    report = run_runtime_scenario("corr-phase6-test")
    assert report.status == "passed"
    assert report.correlation_id == "corr-phase6-test"
    phases = {step["phase"] for step in report.steps}
    assert phases == {1, 2, 3, 4, 5}
    assert report.steps[3]["blocked"] is True
    assert {"marketing", "support", "devops"} <= set(report.steps[4]["departments"])


def test_waiver_marks_gate_waived_when_forced_failure(monkeypatch):
    from phase6 import gate

    original = gate._path_check

    def flaky(check_id, check_type, subject, path, doc_ref):
        if check_id == "phase6-doc-1":
            from phase6.gate import CheckResult

            return CheckResult(check_id, check_type, subject, "failed", "forced", [], doc_ref)
        return original(check_id, check_type, subject, path, doc_ref)

    monkeypatch.setattr(gate, "_path_check", flaky)
    decision = check_phase_gate(run_suites=False, waiver_ref="issue:phase6-temp")
    assert decision.status == "waived"
    explained = explain_failed_check(decision, "phase6-doc-1")
    assert explained["check"]["status"] == "failed"
