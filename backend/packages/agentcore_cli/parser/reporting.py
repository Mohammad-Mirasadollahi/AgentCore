"""``status``, ``inventory``, ``docs-standards``, ``stats``."""

from __future__ import annotations

import argparse

from agentcore_cli.util import add_scope_args


def register(sub: argparse._SubParsersAction) -> None:
    status = sub.add_parser(
        "status",
        help="Show platform + graph sync status (one command)",
    )
    add_scope_args(status, required=False)
    status.add_argument("--json", action="store_true", help="Print full JSON only")
    status.add_argument("--verbose", action="store_true", help="Human summary + JSON")

    inventory = sub.add_parser(
        "inventory",
        help="List code/docs done vs remaining for pinned client software roots",
        epilog="Modes (no dashed flags): agentcore inventory | agentcore inventory detail | "
        "agentcore inventory save <file> | agentcore inventory detail save <file>",
    )
    inventory.add_argument(
        "words",
        nargs="*",
        help="Optional words: detail | save <path> | detail save <path>",
    )

    docs_standards = sub.add_parser(
        "docs-standards",
        help="Report which docs/ Markdown files fail AgentCore documentation standards",
        epilog="Modes (no dashed flags): agentcore docs-standards | agentcore docs-standards detail | "
        "agentcore docs-standards save <file> | agentcore docs-standards detail save <file>",
    )
    docs_standards.add_argument(
        "words",
        nargs="*",
        help="Optional words: detail | save <path> | detail save <path>",
    )

    quality_audit = sub.add_parser(
        "quality-audit",
        help="Categorized quality audit for docs + code (standards, size, linking, sync gaps)",
        epilog="Modes (no dashed flags): agentcore quality-audit | agentcore quality-audit detail | "
        "agentcore quality-audit save | agentcore quality-audit save <file> | "
        "agentcore quality-audit detail save [<file>]",
    )
    quality_audit.add_argument(
        "words",
        nargs="*",
        help="Optional words: detail | save [<path>] | detail save [<path>]",
    )

    docs_suggest = sub.add_parser(
        "docs-suggest-links",
        help="Hybrid evidence-only linked_symbols suggestions (path citations → tokens; no invented edges)",
    )
    docs_suggest.add_argument(
        "--path",
        default="",
        help="Single Markdown file (repo-relative or absolute); default: scan --docs-root",
    )
    docs_suggest.add_argument(
        "--docs-root",
        default="docs",
        help="Directory under repo root to scan when --path is omitted (default: docs)",
    )
    docs_suggest.add_argument(
        "--include-all",
        action="store_true",
        help="Include files with zero new suggestions (already linked / no evidence)",
    )
    docs_suggest.add_argument(
        "--apply",
        action="store_true",
        help="Write suggested tokens into frontmatter linked_symbols (still need agentcore sync)",
    )
    docs_suggest.add_argument(
        "--json",
        action="store_true",
        help="Print JSON report",
    )

    stats = sub.add_parser(
        "stats",
        help="Count code/docs, language mix, and processed vs remaining percents",
        epilog="Modes (no dashed flags): agentcore stats | agentcore stats detail | "
        "agentcore stats save <file> | agentcore stats detail save <file>",
    )
    stats.add_argument(
        "words",
        nargs="*",
        help="Optional words: detail | save <path> | detail save <path>",
    )
