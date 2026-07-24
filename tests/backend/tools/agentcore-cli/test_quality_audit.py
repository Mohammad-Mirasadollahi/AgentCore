"""Tests for agentcore quality-audit."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from agentcore_cli.commands.quality_audit import (
    cmd_quality_audit,
    format_detail_text,
    parse_quality_audit_words,
)
from agentcore_cli.commands.quality_audit.categories import (
    CATEGORY_DOCS_LINKING_GAP,
    CATEGORY_DOCS_REVISION_INVALID,
    CATEGORY_DOCS_REVISION_MISSING,
    CATEGORY_DOCS_STANDARDS,
)
from agentcore_cli.commands.quality_audit.collect import build_quality_audit_report
from agentcore_cli.parser import build_parser


GOOD_DOC = """---
doc_id: ac.doc.test.good
title: "01 - Good Doc"
doc_type: standard
status: active
schema_version: "1.0"
owner: platform-docs
summary: A conforming test document.
tags:
  - test
phase: "00-master-plan"
canonical_path: docs/00-master-plan/01-good-doc.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
  - platform-engineering
authority: normative
visibility: internal
doc_version: "1.0.0"
updated_at: "2026-07-24"
---

# 01 - Good Doc

## Purpose

This document owns the good-doc fixture for CLI tests.

## Related Documents

- none
"""


def test_parser_quality_audit_word_modes():
    parser = build_parser()
    args = parser.parse_args(["quality-audit"])
    assert args.command == "quality-audit"
    assert args.words == []
    detailed = parser.parse_args(["quality-audit", "detail", "save", "/tmp/qa.txt"])
    assert detailed.words == ["detail", "save", "/tmp/qa.txt"]


def test_parse_quality_audit_words_default_save(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "agentcore_cli.commands.quality_audit.words.repo_root",
        lambda: tmp_path,
    )
    detail, path = parse_quality_audit_words(["save"])
    assert detail is False
    assert path.endswith(".txt")
    assert "quality-audit" in path
    with pytest.raises(SystemExit):
        parse_quality_audit_words(["--detail"])


def test_build_quality_audit_report_categorizes_docs(tmp_path: Path, monkeypatch):
    docs = tmp_path / "docs" / "00-master-plan"
    docs.mkdir(parents=True)
    bad = docs / "01-bad.md"
    bad.write_text("# Bad\n\nSee `backend/packages/demo/mod.py` for sync.\n", encoding="utf-8")
    code = tmp_path / "backend" / "packages" / "demo" / "mod.py"
    code.parent.mkdir(parents=True)
    code.write_text("def sync_repo():\n    return 1\n", encoding="utf-8")

    monkeypatch.setattr(
        "agentcore_cli.commands.quality_audit.collect.repo_root",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "agentcore_cli.commands.quality_audit.collect._audit_code",
        lambda _args=None: ([], {"available": False, "error": "skipped in unit test"}),
    )
    report = build_quality_audit_report()
    assert report["summary"]["findings_total"] >= 1
    cats = {c["category"]: c["count"] for c in report["categories"]}
    assert cats.get(CATEGORY_DOCS_STANDARDS, 0) >= 1
    assert cats.get(CATEGORY_DOCS_LINKING_GAP, 0) >= 1
    text = format_detail_text(report, top_only=False)
    assert "docs.standards" in text
    assert "docs.linking_gap" in text


def test_build_quality_audit_report_revision_categories(tmp_path: Path, monkeypatch):
    docs = tmp_path / "docs" / "00-master-plan"
    docs.mkdir(parents=True)
    missing = GOOD_DOC.replace("doc_version: \"1.0.0\"\n", "").replace(
        "updated_at: \"2026-07-24\"\n", ""
    )
    invalid = GOOD_DOC.replace('doc_version: "1.0.0"', 'doc_version: "bad"')
    (docs / "01-missing.md").write_text(missing, encoding="utf-8")
    (docs / "02-invalid.md").write_text(invalid, encoding="utf-8")
    backend_docs = tmp_path / "backend" / "docs"
    backend_docs.mkdir(parents=True)
    (backend_docs / "extra.md").write_text(missing, encoding="utf-8")

    monkeypatch.setattr(
        "agentcore_cli.commands.quality_audit.collect.repo_root",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "agentcore_cli.commands.quality_audit.collect._audit_code",
        lambda _args=None: ([], {"available": False, "error": "skipped in unit test"}),
    )
    report = build_quality_audit_report()
    cats = {c["category"]: c["count"] for c in report["categories"]}
    assert cats.get(CATEGORY_DOCS_REVISION_MISSING, 0) >= 2
    assert cats.get(CATEGORY_DOCS_REVISION_INVALID, 0) >= 1
    paths = {f["path"] for f in report["findings"] if f["category"] == CATEGORY_DOCS_REVISION_MISSING}
    assert "backend/docs/extra.md" in paths


def test_cmd_quality_audit_save(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(
        "agentcore_cli.commands.quality_audit.cmd.build_quality_audit_report",
        lambda _args=None: {
            "ok": True,
            "generated_at": "t",
            "repo": str(tmp_path),
            "summary": {
                "findings_total": 0,
                "docs_findings": 0,
                "code_findings": 0,
                "categories_with_findings": 0,
            },
            "code_audit": {"available": False, "error": "n/a"},
            "categories": [],
            "findings": [],
            "by_category": {},
        },
    )
    out = tmp_path / "out.txt"
    args = argparse.Namespace(words=["save", str(out)])
    assert cmd_quality_audit(args) == 0
    assert out.is_file()
    assert out.with_suffix(".json").is_file()
    captured = capsys.readouterr().out
    assert "Quality audit" in captured
    assert "Saved" in captured
