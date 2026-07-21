#!/usr/bin/env python3
"""Verify ThinkingSOC ai-toolstack agent stack (MCP memory + headroom, ponytail)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cli.log_util import ts_section
from cli.paths import ToolstackPaths
from cli.verify_runner import VerifyRunner

_LIB = Path(__file__).resolve().parents[1]
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify ai-toolstack stack")
    parser.add_argument("--quick", action="store_true", help="Config + symlinks only")
    args = parser.parse_args(argv)

    paths = ToolstackPaths.discover()
    v = VerifyRunner()

    v.section("Agent hub")
    for name in (
        "ai-toolstack.mdc",
        "ponytail.mdc",
        "no-cloud-exfiltration.mdc",
        "root-cause-fix.mdc",
    ):
        v.file_ok(paths.rules / name, f"rule {name}")
        v.symlink_ok(
            paths.repo / ".cursor/rules" / name,
            paths.rules / name,
            f"symlink {name}",
        )

    v.section("Removed components")
    for gone in (
        "graphify.mdc",
        "code-review-graph.mdc",
        "caveman-stack-cursor.mdc",
        "mcp-first-agent.mdc",
        "ponytail-stack-cursor.mdc",
    ):
        if (paths.rules / gone).exists():
            v.fail(f"{gone} should be removed from ai-toolstack/rules")
        else:
            v.pass_(f"{gone} absent")
    graphify_rules_dir = paths.rules / "graphify-out"
    if graphify_rules_dir.exists():
        v.fail("ai-toolstack/rules/graphify-out should be removed")
    else:
        v.pass_("rules/graphify-out absent")

    legacy_lib = paths.ai_toolstack / "lib" / "graphify_enrichment"
    if legacy_lib.is_dir():
        v.fail("lib/graphify_enrichment/ must be removed")
    else:
        v.pass_("lib/graphify_enrichment absent")

    v.section("MCP backends template")
    tpl = paths.config / "mcp-lazy-servers.json.template"
    if tpl.is_file():
        text = tpl.read_text(encoding="utf-8")
        if all(x in text for x in ('"memory"', '"headroom"')) and "graphify" not in text:
            v.pass_("mcp-lazy-servers.json.template (memory + headroom only)")
        else:
            v.fail("unexpected MCP template content")
    else:
        v.fail("mcp-lazy-servers.json.template missing")

    v.section("Ponytail vendor")
    vendor = paths.ai_toolstack / "skills" / "vendor" / "ponytail" / "ponytail" / "SKILL.md"
    v.file_ok(vendor, "vendor ponytail skill")

    caveman_vendor = paths.ai_toolstack / "skills" / "vendor" / "caveman"
    if caveman_vendor.exists():
        v.fail("skills/vendor/caveman must be removed")
    else:
        v.pass_("vendor/caveman absent")

    for gone_skill in ("ponytail-cursor-stack", "persian-chat-reply"):
        path = paths.ai_toolstack / "skills" / "thinkingsoc" / gone_skill
        if path.exists():
            v.fail(f"skills/thinkingsoc/{gone_skill} should be removed (global or doc-only)")
        else:
            v.pass_(f"thinkingsoc/{gone_skill} absent")

    v.section("Legacy runtime paths")
    for link in (
        paths.repo / "graphify-out",
        paths.repo / ".graphify",
        paths.repo / ".code-review-graph",
        paths.repo / ".code-review-graphignore",
    ):
        if link.is_symlink() or link.exists():
            v.fail(f"legacy path still present: {link.relative_to(paths.repo)}")
        else:
            v.pass_(f"{link.name} absent at repo root")

    for rel in (
        "data/graphify-out",
        "data/graphify",
        "data/code-review-graph",
        "graphify-out",
        "lib/graphify-out",
        "rules/graphify-out",
    ):
        p = paths.ai_toolstack / rel
        if p.exists():
            v.fail(f"ai-toolstack/{rel}/ should be removed (run purge-legacy-graph-paths.sh)")
        else:
            v.pass_(f"ai-toolstack/{rel}/ absent")

    local = paths.ai_toolstack / "data" / "local"
    for name in (
        "crg-watch.toml",
        "crg-update-last-line.txt",
        "graphify-watch.service",
        "mcp-lazy-servers.json.bak",
        "sync-last-run.json",
    ):
        p = local / name
        if p.exists():
            v.fail(f"data/local/{name} should be removed (run purge-legacy-graph-paths.sh)")
        else:
            v.pass_(f"data/local/{name} absent")

    ts_section("Summary")
    print(f"  Passed: {v.pass_count}  Warnings: {v.warn_count}  Failed: {v.fail_count}")
    if v.fail_count:
        return 1
    if args.quick:
        v.pass_("--quick (no runtime probes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
