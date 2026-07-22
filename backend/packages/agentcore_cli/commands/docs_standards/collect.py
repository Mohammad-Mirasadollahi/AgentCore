"""Scan docs trees and build a standards compliance report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentcore_cli.commands.docs_standards.check import check_file
from agentcore_cli.commands.inventory.util import TOP_N, pct, top
from agentcore_cli.util import repo_root

DEFAULT_DOC_ROOTS = ("docs",)


def _iter_markdown(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def build_docs_standards_report(
    *,
    roots: list[Path] | None = None,
    repo: Path | None = None,
) -> dict[str, Any]:
    base = (repo or repo_root()).resolve()
    scan_roots = roots or [base / name for name in DEFAULT_DOC_ROOTS]
    findings: list[dict[str, Any]] = []
    for root in scan_roots:
        root = root.resolve()
        if not root.is_dir():
            continue
        for path in _iter_markdown(root):
            # Report paths relative to repo root when under it; else under scan root.
            try:
                findings.append(check_file(path, root=base))
            except ValueError:
                findings.append(check_file(path, root=root))

    conforming = [row for row in findings if row.get("ok")]
    nonconforming = [row for row in findings if not row.get("ok")]
    nonconforming_sorted = sorted(
        nonconforming,
        key=lambda r: (-int(r.get("issue_count") or 0), str(r.get("file") or "")),
    )
    conforming_sorted = sorted(conforming, key=lambda r: str(r.get("file") or ""))
    total = len(findings)
    non_count = len(nonconforming)
    ok_count = len(conforming)
    return {
        "repo": str(base),
        "roots": [str(p.resolve()) for p in scan_roots],
        "summary": {
            "total": total,
            "conforming_count": ok_count,
            "nonconforming_count": non_count,
            "percent_conforming": pct(ok_count, total),
            "percent_nonconforming": pct(non_count, total),
        },
        "nonconforming": nonconforming_sorted,
        "conforming": conforming_sorted,
        "top_nonconforming": top(nonconforming_sorted, n=TOP_N),
        "top_n": TOP_N,
    }
