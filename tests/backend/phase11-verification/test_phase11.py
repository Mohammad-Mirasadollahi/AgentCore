import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUPPORT = ROOT / "tests" / "support"
PACKAGES = ROOT / "backend" / "packages"
for path in (SUPPORT, PACKAGES):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase11.catalog import REQUIRED_DOCS
from phase11.checks import run_all_checks
from phase11.gate import check_phase_gate, explain_failed_check


def test_catalog_includes_acceptance_doc():
    assert any(path.name == "07-phase11-verification-and-acceptance.md" for path in REQUIRED_DOCS)


def test_phase11_gate_passes_docs_and_examples_catalog():
    decision = check_phase_gate()
    assert decision.status == "pass", [item.public() for item in decision.checks if item.status == "failed"]
    report = decision.public()
    assert report["blocked"] is False
    assert report["failed_count"] == 0
    assert report["passed_count"] >= 20


def test_phase11_verification_checks_exit_criteria():
    results = run_all_checks()
    assert results
    assert all(item.status == "passed" for item in results), [
        item.public() for item in results if item.status != "passed"
    ]
    types = {item.check_type for item in results}
    assert {"examples_catalog", "coverage", "example_shape", "checklist", "mapping"} <= types


def test_waiver_marks_gate_waived_when_forced_failure(monkeypatch):
    from phase11 import gate

    original = gate._path_check

    def flaky(check_id, check_type, subject, path, doc_ref):
        if check_id == "phase11-doc-1":
            return gate.CheckResult(check_id, check_type, subject, "failed", "forced", [], doc_ref)
        return original(check_id, check_type, subject, path, doc_ref)

    monkeypatch.setattr(gate, "_path_check", flaky)
    decision = check_phase_gate(waiver_ref="issue:phase11-temp")
    assert decision.status == "waived"
    explained = explain_failed_check(decision, "phase11-doc-1")
    assert explained["check"]["status"] == "failed"
