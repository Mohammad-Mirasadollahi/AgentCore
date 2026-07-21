"""Tests for token-stats report formatting helpers."""

from __future__ import annotations

import unittest

from token_stats.report import (
    ComponentTotals,
    Report,
    active_no_save_components,
    aggregate_events,
    effective_tokens_in,
    save_pct,
)


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for name in sorted(globals()):
        if not name.startswith("test_"):
            continue
        fn = globals()[name]
        if callable(fn):
            suite.addTest(unittest.FunctionTestCase(fn))
    return suite


def test_effective_tokens_in_uses_logged_value() -> None:
    assert effective_tokens_in({"tokens_in": 23, "tokens_out": 34}) == 23


def test_effective_tokens_in_from_meta_bytes() -> None:
    row = {"tokens_in": 0, "tokens_out": 34, "meta": {"in_bytes": 92}}
    assert effective_tokens_in(row) == 23


def test_effective_tokens_in_from_out_plus_saved() -> None:
    row = {"tokens_out": 200, "tokens_saved": 3550}
    assert effective_tokens_in(row) == 3750


def test_aggregate_unknown_component_still_counted() -> None:
    events = [
        {
            "component": "removed-stack",
            "tokens_out": 200,
            "tokens_saved": 3550,
        }
    ]
    totals = aggregate_events(events)
    assert totals["removed-stack"].tokens_in == 3750
    assert totals["removed-stack"].tokens_saved == 3550


def test_save_pct_uses_input_when_present() -> None:
    assert save_pct(tokens_in=100, tokens_out=20, tokens_saved=80) == 80.0


def test_save_pct_uses_out_plus_saved_when_input_zero() -> None:
    pct = save_pct(tokens_in=0, tokens_out=200, tokens_saved=3550)
    assert 94.6 <= pct <= 94.7


def test_save_pct_uses_out_plus_saved_when_saved_exceeds_in() -> None:
    pct = save_pct(tokens_in=26600, tokens_out=1787, tokens_saved=171900)
    assert 98.9 <= pct <= 99.1


def test_save_pct_zero_when_no_savings() -> None:
    assert save_pct(tokens_in=100, tokens_out=100, tokens_saved=0) == 0.0


def test_effective_tokens_in_uses_out_when_no_save() -> None:
    row = {"tokens_out": 500, "tokens_saved": 0}
    assert effective_tokens_in(row) == 500


def test_active_no_save_lists_used_zero_save_components() -> None:
    report = Report(
        range_label="test",
        components={
            "memory": ComponentTotals(
                component="memory", calls=2, tokens_in=46, tokens_out=68, tokens_saved=0
            ),
            "ponytail": ComponentTotals(
                component="ponytail", calls=1, tokens_in=3750, tokens_out=200, tokens_saved=3550
            ),
        },
    )
    active = active_no_save_components(report)
    names = [a["component"] for a in active]
    assert "memory" in names
    assert "ponytail" not in names


def test_aggregate_ponytail_component() -> None:
    events = [
        {
            "component": "ponytail",
            "tokens_in": 130,
            "tokens_out": 80,
            "tokens_saved": 50,
        }
    ]
    totals = aggregate_events(events)
    assert totals["ponytail"].tokens_saved == 50
    assert "ponytail" in __import__(
        "token_stats.report", fromlist=["DISPLAY_ORDER"]
    ).DISPLAY_ORDER


def test_total_save_pct_uses_out_plus_saved() -> None:
    report = Report(
        range_label="test",
        rtk={"tokens_in": 1000, "tokens_out": 200, "tokens_saved": 800, "savings_pct": 80.0},
        headroom={"tokens_in": 0, "tokens_out": 0, "tokens_saved": 0},
    )
    assert report.total_save_pct() == 80.0
