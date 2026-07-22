"""Tests for agentcore docs-standards."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from agentcore_cli.commands.docs_standards import (
    cmd_docs_standards,
    format_detail_text,
    parse_docs_standards_words,
)
from agentcore_cli.commands.docs_standards.check import check_markdown_doc
from agentcore_cli.commands.docs_standards.collect import build_docs_standards_report
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
---

# 01 - Good Doc

## Purpose

This document owns the good-doc fixture for CLI tests.

## Related Documents

- none
"""


def test_parser_docs_standards_word_modes():
    parser = build_parser()
    args = parser.parse_args(["docs-standards"])
    assert args.command == "docs-standards"
    assert args.words == []

    detailed = parser.parse_args(["docs-standards", "detail"])
    assert detailed.words == ["detail"]

    saved = parser.parse_args(["docs-standards", "save", "/tmp/out.txt"])
    assert saved.words == ["save", "/tmp/out.txt"]

    both = parser.parse_args(["docs-standards", "detail", "save", "/tmp/out.txt"])
    assert both.words == ["detail", "save", "/tmp/out.txt"]


def test_parse_docs_standards_words():
    assert parse_docs_standards_words([]) == (False, "")
    assert parse_docs_standards_words(["detail"]) == (True, "")
    assert parse_docs_standards_words(["save", "/tmp/a.txt"]) == (False, "/tmp/a.txt")
    assert parse_docs_standards_words(["detail", "save", "/tmp/a.txt"]) == (True, "/tmp/a.txt")
    with pytest.raises(SystemExit):
        parse_docs_standards_words(["save"])
    with pytest.raises(SystemExit):
        parse_docs_standards_words(["--detail"])


def test_check_markdown_doc_ok_and_fail():
    ok = check_markdown_doc(
        relative_path="docs/00-master-plan/01-good-doc.md",
        text=GOOD_DOC,
    )
    assert ok["ok"] is True
    assert ok["issue_count"] == 0

    bad = check_markdown_doc(relative_path="docs/x.md", text="# Only H1\n\nNo frontmatter.\n")
    assert bad["ok"] is False
    assert "missing_or_invalid_frontmatter" in bad["issues"]


def test_check_ignores_h1_inside_fences():
    text = GOOD_DOC.replace(
        "## Related Documents\n\n- none\n",
        "## Related Documents\n\n```yaml\n# NN - Example Title\n```\n\n- none\n",
    )
    row = check_markdown_doc(
        relative_path="docs/00-master-plan/01-good-doc.md",
        text=text,
    )
    assert row["ok"] is True
    assert "multiple_h1" not in row["issues"]


def test_build_report_percent(tmp_path: Path):
    docs = tmp_path / "docs" / "00-master-plan"
    docs.mkdir(parents=True)
    (docs / "01-good-doc.md").write_text(GOOD_DOC, encoding="utf-8")
    (docs / "02-bad.md").write_text("# Bad\n", encoding="utf-8")
    report = build_docs_standards_report(roots=[tmp_path / "docs"], repo=tmp_path)
    assert report["summary"]["total"] == 2
    assert report["summary"]["conforming_count"] == 1
    assert report["summary"]["nonconforming_count"] == 1
    assert report["summary"]["percent_nonconforming"] == 50.0
    assert report["nonconforming"][0]["file"] == "docs/00-master-plan/02-bad.md"


def test_format_detail_text_and_save(tmp_path: Path, monkeypatch, capsys):
    report = {
        "repo": str(tmp_path),
        "roots": [str(tmp_path / "docs")],
        "summary": {
            "total": 2,
            "conforming_count": 1,
            "nonconforming_count": 1,
            "percent_conforming": 50.0,
            "percent_nonconforming": 50.0,
        },
        "nonconforming": [
            {
                "file": "docs/a.md",
                "ok": False,
                "issue_count": 1,
                "issues": ["missing_or_invalid_frontmatter"],
                "doc_id": None,
                "doc_type": None,
                "status": None,
            }
        ],
        "conforming": [{"file": "docs/b.md", "ok": True, "issue_count": 0, "issues": []}],
        "top_nonconforming": [
            {
                "file": "docs/a.md",
                "ok": False,
                "issue_count": 1,
                "issues": ["missing_or_invalid_frontmatter"],
                "doc_id": None,
                "doc_type": None,
                "status": None,
            }
        ],
        "top_n": 10,
    }
    text = format_detail_text(report)
    assert "50.0%" in text
    assert "docs/a.md" in text
    assert "missing_or_invalid_frontmatter" in text

    monkeypatch.setattr(
        "agentcore_cli.commands.docs_standards.cmd.build_docs_standards_report",
        lambda: report,
    )
    out = tmp_path / "details.txt"
    args = argparse.Namespace(words=["detail", "save", str(out)])
    assert cmd_docs_standards(args) == 0
    saved = out.read_text(encoding="utf-8")
    assert "docs/a.md" in saved
    captured = capsys.readouterr().out
    assert "Docs standards" in captured
    assert "Saved" in captured
