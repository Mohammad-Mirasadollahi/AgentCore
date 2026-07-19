from __future__ import annotations

from typing import Any
from uuid import uuid4

from . import _paths  # noqa: F401 — side effect: service path bootstrap

from .platform import PlatformBackends


def docs_status(
    backends: PlatformBackends,
    *,
    scope: dict[str, str],
    base: dict[str, Any],
) -> dict[str, Any]:
    docs_scope = backends.docs_scope(scope)
    coverage = backends.docs.get_doc_coverage(docs_scope)
    missing = backends.docs.find_missing_docs(docs_scope)
    return {
        **base,
        "coverage": coverage,
        "missing": missing,
        "missing_count": len(missing),
    }


def docs_drift_check(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    symbol = str(arguments.get("symbol") or "").strip()
    if not symbol:
        raise ValueError("symbol is required")
    file_path = arguments.get("file_path")
    symbol_id = backends.ensure_docs_symbol(scope, symbol, str(file_path) if file_path else None)
    findings = backends.docs.detect_drift(
        backends.docs_scope(scope),
        backends.actor_id,
        correlation_id,
        f"mcp-drift:{correlation_id}",
        symbol_ids=[symbol_id],
    )
    return {
        **base,
        "symbol": symbol,
        "file_path": file_path,
        "symbol_id": symbol_id,
        "drift": bool(findings),
        "findings": [item.public() for item in findings],
    }


def docs_write(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    mode = str(arguments.get("mode") or "").strip().lower()
    if mode not in {"validate", "note", "draft", "index"}:
        raise ValueError("mode must be one of: validate, note, draft, index")

    docs_scope = backends.docs_scope(scope)
    title = str(arguments.get("title") or "").strip()
    body = str(arguments.get("body") or "").strip()
    symbol = str(arguments.get("symbol") or "").strip()
    file_path = str(arguments.get("file_path") or "").strip() or None
    owner = str(arguments.get("owner") or backends.actor_id).strip() or backends.actor_id
    status = str(arguments.get("status") or "draft").strip() or "draft"
    path = str(arguments.get("path") or "").strip()
    custom_fm = arguments.get("frontmatter") if isinstance(arguments.get("frontmatter"), dict) else None

    if mode == "validate":
        frontmatter = custom_fm or build_frontmatter(
            title=title or "Untitled",
            owner=owner,
            status=status,
            doc_id=str(arguments.get("doc_id") or "").strip() or None,
            linked_symbols=[symbol] if symbol else [],
        )
        errors = backends.docs.validate_frontmatter(frontmatter)
        return {
            **base,
            "mode": "validate",
            "ok": not errors,
            "errors": errors,
            "frontmatter": frontmatter,
        }

    if mode == "draft":
        if not title or not body:
            raise ValueError("draft mode requires title and body")
        if not symbol:
            raise ValueError("draft mode requires symbol")
        symbol_id = backends.ensure_docs_symbol(scope, symbol, file_path)
        draft = backends.docs.create_draft(
            docs_scope,
            backends.actor_id,
            correlation_id,
            f"mcp-docs-draft:{correlation_id}",
            {
                "symbol_id": symbol_id,
                "title": title,
                "body": body,
            },
        )
        return {
            **base,
            "mode": "draft",
            "written": "draft",
            "symbol": symbol,
            "symbol_id": symbol_id,
            "draft": draft.public(),
        }

    if mode in {"note", "index"}:
        if not title or not body:
            raise ValueError(f"{mode} mode requires title and body")
        linked: list[str] = []
        symbol_id = None
        if symbol:
            symbol_id = backends.ensure_docs_symbol(scope, symbol, file_path)
            linked = [symbol]
        if not path:
            slug = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in title.lower()).strip("-") or "note"
            path = f"docs/cursor/{slug}.md"
        frontmatter = custom_fm or build_frontmatter(
            title=title,
            owner=owner,
            status=status if mode == "index" else "draft",
            doc_id=str(arguments.get("doc_id") or "").strip() or None,
            linked_symbols=linked,
        )
        errors = backends.docs.validate_frontmatter(frontmatter)
        if errors:
            raise ValueError("frontmatter validation failed: " + "; ".join(errors))
        document = backends.docs.index_document(
            docs_scope,
            backends.actor_id,
            correlation_id,
            f"mcp-docs-{mode}:{correlation_id}",
            {
                "path": path,
                "frontmatter": frontmatter,
                "body": body,
            },
        )
        anchor = None
        if symbol_id:
            symbol_row = backends.docs.store.get_symbol(symbol_id, docs_scope)
            anchor = backends.docs.register_anchor(
                docs_scope,
                backends.actor_id,
                correlation_id,
                f"mcp-docs-anchor:{correlation_id}",
                {
                    "doc_id": document.id,
                    "symbol_id": symbol_id,
                    "recorded_hash": symbol_row.body_hash,
                },
            )
        return {
            **base,
            "mode": mode,
            "written": "document",
            "path": path,
            "symbol": symbol or None,
            "symbol_id": symbol_id,
            "document": document.public(),
            "anchor": anchor.public() if anchor is not None else None,
        }

    raise ValueError(f"unsupported docs write mode: {mode}")


def build_frontmatter(
    *,
    title: str,
    owner: str,
    status: str,
    doc_id: str | None,
    linked_symbols: list[str],
) -> dict[str, Any]:
    return {
        "doc_id": doc_id or f"doc_{uuid4().hex[:12]}",
        "title": title,
        "owner": owner,
        "status": status,
        "schema_version": "1.0",
        "linked_symbols": list(linked_symbols),
        "decision_refs": [],
    }
