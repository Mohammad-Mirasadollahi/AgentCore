"""Build categorized quality-audit report (docs + code)."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from agentcore_cli.commands.docs_standards.check import (
    DESIGN_TYPES,
    SOFT_BODY_LINES,
    check_markdown_doc,
)
from agentcore_cli.commands.docs_standards.collect import (
    DEFAULT_DOC_ROOTS,
    build_docs_standards_report,
)
from agentcore_cli.commands.quality_audit.categories import (
    CATEGORY_CODE_LOW_SYMBOL_DOCS,
    CATEGORY_CODE_NEVER_INGESTED,
    CATEGORY_CODE_STALE_EDITED,
    CATEGORY_DOCS_FLOW_TABLE,
    CATEGORY_DOCS_LANE_INVALID,
    CATEGORY_DOCS_LINKING_GAP,
    CATEGORY_DOCS_REVISION_INVALID,
    CATEGORY_DOCS_REVISION_MISSING,
    CATEGORY_DOCS_SIZE_HARD,
    CATEGORY_DOCS_SIZE_SOFT,
    CATEGORY_DOCS_STANDARDS,
    CATEGORY_META,
    VALID_CONCERNS,
)

_REVISION_ISSUES = frozenset({"invalid_doc_version", "invalid_updated_at"})
_REVISION_WARN_PREFIXES = (
    "missing_recommended:doc_version",
    "missing_recommended:updated_at",
)
from agentcore_cli.docs_link_suggest import extract_evidence_link_tokens
from agentcore_cli.markdown_frontmatter import parse_markdown_frontmatter
from agentcore_cli.util import now_iso, repo_root

FLOW_TABLE_RE = re.compile(r"(?im)^\|.+\b(step|actor|action|outcome)\b.+\|")


def _finding(
    *,
    category: str,
    path: str,
    detail: str,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    meta = CATEGORY_META[category]
    return {
        "category": category,
        "severity": meta["severity"],
        "title": meta["title"],
        "path": path,
        "detail": detail,
        "evidence": list(evidence or []),
        "fix_hint": meta["fix_hint"],
    }


def _cited_path_tokens(body: str, *, root: Path) -> list[str]:
    return extract_evidence_link_tokens(body, repo=root, max_tokens=64)


def _iter_product_docs(root: Path):
    for name in DEFAULT_DOC_ROOTS:
        base = root / name
        if not base.is_dir():
            continue
        yield from sorted(p for p in base.rglob("*.md") if p.is_file())


def _audit_docs(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    standards = build_docs_standards_report(repo=root)
    for row in (standards.get("nonconforming") or []) + (standards.get("conforming") or []):
        path = str(row.get("file") or "")
        issues = [str(i) for i in (row.get("issues") or [])]
        warnings = [str(w) for w in (row.get("warnings") or [])]
        if not path:
            continue

        rev_issues = [i for i in issues if i in _REVISION_ISSUES]
        hard = [i for i in issues if i.startswith("body_over_hard_budget")]
        other = [
            i
            for i in issues
            if i not in _REVISION_ISSUES and not i.startswith("body_over_hard_budget")
        ]
        if hard:
            findings.append(
                _finding(
                    category=CATEGORY_DOCS_SIZE_HARD,
                    path=path,
                    detail="; ".join(hard),
                    evidence=hard,
                )
            )
        if rev_issues:
            findings.append(
                _finding(
                    category=CATEGORY_DOCS_REVISION_INVALID,
                    path=path,
                    detail="; ".join(rev_issues),
                    evidence=rev_issues,
                )
            )
        if other:
            findings.append(
                _finding(
                    category=CATEGORY_DOCS_STANDARDS,
                    path=path,
                    detail="; ".join(other),
                    evidence=other,
                )
            )
        rev_warns = [
            w
            for w in warnings
            if any(w.startswith(p) for p in _REVISION_WARN_PREFIXES)
        ]
        if rev_warns:
            findings.append(
                _finding(
                    category=CATEGORY_DOCS_REVISION_MISSING,
                    path=path,
                    detail="; ".join(rev_warns),
                    evidence=rev_warns,
                )
            )

    for path in _iter_product_docs(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        text = path.read_text(encoding="utf-8", errors="replace")
        row = check_markdown_doc(relative_path=rel, text=text)
        for warning in row.get("warnings") or []:
            if str(warning).startswith("body_over_soft_budget"):
                findings.append(
                    _finding(
                        category=CATEGORY_DOCS_SIZE_SOFT,
                        path=rel,
                        detail=str(warning),
                        evidence=[str(warning)],
                    )
                )
        fm, body = parse_markdown_frontmatter(text)
        concern = str((fm or {}).get("concern_lane") or "").strip()
        if concern and concern not in VALID_CONCERNS:
            findings.append(
                _finding(
                    category=CATEGORY_DOCS_LANE_INVALID,
                    path=rel,
                    detail=f"concern_lane={concern!r} not in closed set",
                    evidence=[concern],
                )
            )
        existing = {
            str(x).strip()
            for x in ((fm or {}).get("linked_symbols") or [])
            if isinstance((fm or {}).get("linked_symbols"), list) and str(x).strip()
        }
        cited = _cited_path_tokens(body, root=root)
        missing = [t for t in cited if t not in existing]
        if cited and (not existing or missing):
            findings.append(
                _finding(
                    category=CATEGORY_DOCS_LINKING_GAP,
                    path=rel,
                    detail=(
                        "cited code paths lack linked_symbols"
                        if not existing
                        else f"missing {len(missing)} linked token(s)"
                    ),
                    evidence=missing[:12] or cited[:12],
                )
            )
        doc_type = str((fm or {}).get("doc_type") or "")
        if (
            doc_type in DESIGN_TYPES
            and "```mermaid" in body.lower()
            and not FLOW_TABLE_RE.search(body)
        ):
            findings.append(
                _finding(
                    category=CATEGORY_DOCS_FLOW_TABLE,
                    path=rel,
                    detail="design Mermaid present without Step/Actor flow table",
                )
            )
    return findings


def _audit_code(args: Any | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Best-effort code inventory findings; empty if roots/filters unavailable."""
    meta: dict[str, Any] = {"available": False, "error": ""}
    findings: list[dict[str, Any]] = []
    try:
        import argparse

        from agentcore_cli.commands.inventory.collect import build_inventory_report
    except Exception as exc:  # noqa: BLE001
        meta["error"] = f"imports failed: {exc}"
        return findings, meta

    try:
        ns = args if args is not None else argparse.Namespace()
        report = build_inventory_report(ns)
    except Exception as exc:  # noqa: BLE001
        meta["error"] = str(exc)
        return findings, meta

    meta["available"] = True
    meta["paths"] = list(report.get("paths") or [])
    meta["summary"] = report.get("summary") or {}

    remaining_paths: list[str] = []
    edited_paths: list[str] = []
    low_doc_paths: list[tuple[str, str]] = []
    for root_row in report.get("results") or []:
        if not isinstance(root_row, dict):
            continue
        code = root_row.get("code") or {}
        for item in code.get("remaining_files") or []:
            path = _item_path(item)
            if path:
                remaining_paths.append(path)
        for item in code.get("edited_files") or []:
            path = _item_path(item)
            if path:
                edited_paths.append(path)
        for item in code.get("done_files") or []:
            if not isinstance(item, dict):
                continue
            path = _item_path(item)
            sym_total = int(item.get("symbols") or 0)
            sym_docs = int(item.get("documented") or 0)
            if path and sym_total >= 5 and sym_docs * 2 < sym_total:
                low_doc_paths.append(
                    (path, f"documented {sym_docs}/{sym_total} symbols")
                )

    for path in remaining_paths[:200]:
        findings.append(
            _finding(
                category=CATEGORY_CODE_NEVER_INGESTED,
                path=path,
                detail="not ingested into code graph",
            )
        )
    for path in edited_paths[:200]:
        findings.append(
            _finding(
                category=CATEGORY_CODE_STALE_EDITED,
                path=path,
                detail="content changed since last ingest",
            )
        )
    for path, detail in low_doc_paths[:100]:
        findings.append(
            _finding(
                category=CATEGORY_CODE_LOW_SYMBOL_DOCS,
                path=path,
                detail=detail,
            )
        )
    return findings, meta


def _item_path(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        return str(
            item.get("path")
            or item.get("file")
            or item.get("relative_path")
            or ""
        ).strip()
    return ""


def build_quality_audit_report(args: Any | None = None) -> dict[str, Any]:
    root = repo_root().resolve()
    docs_findings = _audit_docs(root)
    code_findings, code_meta = _audit_code(args)
    findings = docs_findings + code_findings
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in findings:
        by_category[str(row["category"])].append(row)

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    findings_sorted = sorted(
        findings,
        key=lambda r: (
            severity_rank.get(str(r.get("severity")), 9),
            str(r.get("category")),
            str(r.get("path")),
        ),
    )
    category_summary = []
    for cat_id, meta in CATEGORY_META.items():
        rows = by_category.get(cat_id) or []
        category_summary.append(
            {
                "category": cat_id,
                "title": meta["title"],
                "severity": meta["severity"],
                "meaning": meta["meaning"],
                "fix_hint": meta["fix_hint"],
                "count": len(rows),
            }
        )
    category_summary.sort(key=lambda r: (-int(r["count"]), severity_rank.get(r["severity"], 9)))

    return {
        "ok": True,
        "generated_at": now_iso(),
        "repo": str(root),
        "summary": {
            "findings_total": len(findings),
            "docs_findings": len(docs_findings),
            "code_findings": len(code_findings),
            "categories_with_findings": sum(1 for c in category_summary if int(c["count"]) > 0),
            "soft_budget_lines": SOFT_BODY_LINES,
        },
        "code_audit": code_meta,
        "categories": category_summary,
        "findings": findings_sorted,
        "by_category": {k: v for k, v in sorted(by_category.items())},
    }
