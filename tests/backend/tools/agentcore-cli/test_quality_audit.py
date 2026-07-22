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
    CATEGORY_DOCS_STANDARDS,
)
from agentcore_cli.commands.quality_audit.collect import build_quality_audit_report
from agentcore_cli.parser import build_parser


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
