"""Scan docs trees and build a standards compliance report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentcore_cli.commands.docs_standards.check import check_file
from agentcore_cli.commands.inventory.util import TOP_N, pct, top
from agentcore_cli.util import repo_root

DEFAULT_DOC_ROOTS = (
    "docs",
    "backend/docs",
    "frontend/docs",
    "deploy-toolkit",
)


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

    revision_debt: list[dict[str, Any]] = []
    for row in findings:
        warns = [str(w) for w in (row.get("warnings") or [])]
        issues = [str(i) for i in (row.get("issues") or [])]
        rev_warns = [w for w in warns if w.startswith("missing_recommended:doc_version") or w.startswith("missing_recommended:updated_at")]
        rev_issues = [i for i in issues if i in {"invalid_doc_version", "invalid_updated_at"}]
        if not rev_warns and not rev_issues:
            continue
        revision_debt.append(
            {
                "file": row.get("file"),
                "doc_id": row.get("doc_id"),
                "doc_version": row.get("doc_version"),
                "updated_at": row.get("updated_at"),
                "warnings": rev_warns,
                "issues": rev_issues,
                "ok": bool(row.get("ok")),
            }
        )
    revision_debt.sort(key=lambda r: str(r.get("file") or ""))

    total = len(findings)
    non_count = len(nonconforming)
    ok_count = len(conforming)
    rev_count = len(revision_debt)
    return {
        "repo": str(base),
        "roots": [str(p.resolve()) for p in scan_roots],
        "summary": {
            "total": total,
            "conforming_count": ok_count,
            "nonconforming_count": non_count,
            "percent_conforming": pct(ok_count, total),
            "percent_nonconforming": pct(non_count, total),
            "revision_debt_count": rev_count,
            "percent_revision_debt": pct(rev_count, total),
        },
        "nonconforming": nonconforming_sorted,
        "conforming": conforming_sorted,
        "revision_debt": revision_debt,
        "top_revision_debt": top(revision_debt, n=TOP_N),
        "top_nonconforming": top(nonconforming_sorted, n=TOP_N),
        "top_n": TOP_N,
    }
