"""Tests for agentcore stats."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

from agentcore_cli.commands.inventory.collect import language_breakdown
from agentcore_cli.commands.stats import cmd_stats, format_bytes, format_detail_text, parse_stats_words
from agentcore_cli.parser import build_parser


def test_parser_stats_word_modes():
    parser = build_parser()
    args = parser.parse_args(["stats"])
    assert args.command == "stats"
    assert args.words == []
    assert parser.parse_args(["stats", "detail"]).words == ["detail"]
    assert parser.parse_args(["stats", "save", "/tmp/s.txt"]).words == ["save", "/tmp/s.txt"]


def test_parse_stats_words():
    assert parse_stats_words([]) == (False, "")
    assert parse_stats_words(["detail", "save", "/tmp/a.txt"]) == (True, "/tmp/a.txt")
    with pytest.raises(SystemExit):
        parse_stats_words(["save"])


def test_format_bytes():
    assert format_bytes(500) == "500 B"
    assert format_bytes(2048).endswith("KB")


def test_language_breakdown_percent():
    discovered = [
        SimpleNamespace(relative_path="a.py", language="python", size_bytes=100),
        SimpleNamespace(relative_path="b.py", language="python", size_bytes=100),
        SimpleNamespace(relative_path="c.ts", language="typescript", size_bytes=50),
    ]
    rows = language_breakdown(
        discovered,
        done=["a.py"],
        edited=["b.py"],
        remaining=["c.ts"],
    )
    by_lang = {r["language"]: r for r in rows}
    assert by_lang["python"]["files"] == 2
    assert by_lang["python"]["percent_of_code"] == 66.7
    assert by_lang["python"]["done_count"] == 1
    assert by_lang["python"]["edited_count"] == 1
    assert by_lang["typescript"]["files"] == 1
    assert by_lang["typescript"]["percent_of_code"] == 33.3
    assert by_lang["typescript"]["remaining_count"] == 1


def test_cmd_stats_save(tmp_path: Path, monkeypatch, capsys):
    report = {
        "scope": {"tenant": "t", "workspace": "w", "project": "p"},
        "paths": [str(tmp_path)],
        "processing": {},
        "models_used": [],
        "totals": {"code_files": 3, "code_bytes": 250, "docs_files": 1, "docs_bytes": 10},
        "languages": [
            {
                "language": "python",
                "files": 2,
                "bytes": 200,
                "percent_of_code": 66.7,
                "percent_of_bytes": 80.0,
                "done_count": 1,
                "edited_count": 0,
                "remaining_count": 1,
                "percent_done": 50.0,
                "percent_edited": 0.0,
                "percent_remaining": 50.0,
            }
        ],
        "summary": {
            "code": {
                "done_count": 1,
                "edited_count": 0,
                "remaining_count": 2,
                "total": 3,
                "percent_done": 33.3,
                "percent_edited": 0.0,
                "percent_remaining": 66.7,
            },
            "docs": {
                "done_count": 0,
                "edited_count": 0,
                "remaining_count": 1,
                "total": 1,
                "percent_done": 0.0,
                "percent_edited": 0.0,
                "percent_remaining": 100.0,
            },
            "llm": {"done_count": 0, "remaining_count": 1, "total": 1, "percent_done": 0.0},
        },
        "results": [
            {
                "path": str(tmp_path),
                "totals": {"code_files": 3, "code_bytes": 250, "docs_files": 1, "docs_bytes": 10},
                "languages": [
                    {
                        "language": "python",
                        "files": 2,
                        "bytes": 200,
                        "percent_of_code": 66.7,
                        "percent_of_bytes": 80.0,
                        "done_count": 1,
                        "edited_count": 0,
                        "remaining_count": 1,
                        "percent_done": 50.0,
                        "percent_edited": 0.0,
                        "percent_remaining": 50.0,
                    }
                ],
            }
        ],
    }
    monkeypatch.setattr(
        "agentcore_cli.commands.stats.cmd.build_inventory_report",
        lambda _args: report,
    )
    out = tmp_path / "stats.txt"
    assert cmd_stats(argparse.Namespace(words=["detail", "save", str(out)])) == 0
    text = out.read_text(encoding="utf-8")
    assert "python" in text
    assert "66.7%" in text
    captured = capsys.readouterr().out
    assert "Stats" in captured
    assert "Saved" in captured
    assert "By language" in format_detail_text(report)


def test_print_sync_preflight(capsys, monkeypatch):
    from agentcore_cli.commands.stats.render import print_sync_preflight

    monkeypatch.setattr("agentcore_cli.ui._use_color", lambda: False)
    report = {
        "scope": {"tenant": "mir", "workspace": "dev", "project": "agentcore"},
        "paths": ["/opt/AgentCore"],
        "totals": {"code_files": 100, "code_bytes": 50000, "docs_files": 20, "docs_bytes": 8000},
        "languages": [
            {
                "language": "python",
                "files": 80,
                "bytes": 40000,
                "percent_of_code": 80.0,
                "percent_of_bytes": 80.0,
                "done_count": 10,
                "edited_count": 5,
                "remaining_count": 65,
                "percent_done": 12.5,
                "percent_edited": 6.2,
                "percent_remaining": 81.2,
            }
        ],
        "summary": {
            "code": {
                "done_count": 10,
                "edited_count": 5,
                "remaining_count": 85,
                "total": 100,
                "percent_done": 10.0,
                "percent_edited": 5.0,
                "percent_remaining": 85.0,
            },
            "docs": {
                "done_count": 2,
                "edited_count": 1,
                "remaining_count": 17,
                "total": 20,
                "percent_done": 10.0,
                "percent_edited": 5.0,
                "percent_remaining": 85.0,
            },
            "llm": {"done_count": 3, "remaining_count": 7, "total": 10, "percent_done": 30.0},
        },
    }
    print_sync_preflight(report)
    out = capsys.readouterr().out
    assert "Before sync" in out
    assert "100 files" in out
    assert "20 files" in out
    assert "Code edited" in out or "edited" in out.lower()
    assert "5/100" in out
    assert "needs sync" in out
    assert "python" in out
    assert "agentcore stats detail" not in out
