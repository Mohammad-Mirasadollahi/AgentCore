"""`agentcore quality-audit` CLI entrypoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentcore_cli import ui
from agentcore_cli.commands.quality_audit.collect import build_quality_audit_report
from agentcore_cli.commands.quality_audit.render import format_detail_text, print_human
from agentcore_cli.commands.quality_audit.words import parse_quality_audit_words


def cmd_quality_audit(args: argparse.Namespace) -> int:
    detail, save_path = parse_quality_audit_words(getattr(args, "words", None))
    report = build_quality_audit_report(args)
    out_path = Path(save_path).expanduser() if save_path else None
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(format_detail_text(report, top_only=False), encoding="utf-8")
        json_path = out_path.with_suffix(".json")
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print_human(report, detail=detail)
    if out_path is not None:
        ui.kv("Saved", str(out_path.resolve()))
        ui.kv("JSON", str(out_path.with_suffix(".json").resolve()))
        ui.blank()

    # Non-zero when findings exist so CI/scripts can gate on quality debt.
    return 1 if int((report.get("summary") or {}).get("findings_total") or 0) > 0 else 0
