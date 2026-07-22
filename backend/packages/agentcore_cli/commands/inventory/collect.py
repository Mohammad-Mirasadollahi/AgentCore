"""Build inventory report from graph + filesystem discovery."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

from agentcore_cli.commands.graph import _graph_scope, _graph_service
from agentcore_cli.commands.inventory.edited import classify_edited_paths
from agentcore_cli.commands.inventory.processing import embed_models_by_symbol, processing_context
from agentcore_cli.commands.inventory.util import (
    CODE_KINDS,
    DOCUMENTED,
    bucket,
    file_row,
    norm_rel,
    pct,
    rel_under,
    sort_done,
    sort_remaining,
    status_bucket,
    top,
)
from agentcore_cli.software_paths import require_software_paths
from agentcore_cli.sync_config import resolve_sync_filters


def language_breakdown(
    discovered_code: list[Any],
    *,
    done: set[str] | list[str],
    edited: set[str] | list[str],
    remaining: set[str] | list[str],
) -> list[dict[str, Any]]:
    """Per-language file counts, bytes, and processing status among discovered code."""
    done_set = {norm_rel(p) for p in done}
    edited_set = {norm_rel(p) for p in edited}
    remaining_set = {norm_rel(p) for p in remaining}
    buckets: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "files": 0,
            "bytes": 0,
            "done_count": 0,
            "edited_count": 0,
            "remaining_count": 0,
        }
    )
    for item in discovered_code:
        rel = norm_rel(item.relative_path)
        lang = str(getattr(item, "language", None) or "unknown").strip() or "unknown"
        row = buckets[lang]
        row["files"] += 1
        row["bytes"] += int(getattr(item, "size_bytes", 0) or 0)
        if rel in done_set:
            row["done_count"] += 1
        elif rel in edited_set:
            row["edited_count"] += 1
        elif rel in remaining_set:
            row["remaining_count"] += 1
        else:
            row["remaining_count"] += 1
    total_files = sum(int(b["files"]) for b in buckets.values())
    total_bytes = sum(int(b["bytes"]) for b in buckets.values())
    out: list[dict[str, Any]] = []
    for language, row in sorted(buckets.items(), key=lambda kv: (-int(kv[1]["files"]), kv[0])):
        files = int(row["files"])
        nbytes = int(row["bytes"])
        out.append(
            {
                "language": language,
                "files": files,
                "bytes": nbytes,
                "percent_of_code": pct(files, total_files),
                "percent_of_bytes": pct(nbytes, total_bytes),
                "done_count": int(row["done_count"]),
                "edited_count": int(row["edited_count"]),
                "remaining_count": int(row["remaining_count"]),
                "percent_done": pct(int(row["done_count"]), files),
                "percent_edited": pct(int(row["edited_count"]), files),
                "percent_remaining": pct(int(row["remaining_count"]), files),
            }
        )
    return out


def inventory_one_root(
    *,
    svc: Any,
    scope: Any,
    root_path: Path,
    max_files: int,
    processing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from code_graph_service.domain.enums import SymbolKind

    from agentcore_cli.commands.inventory.discover import discover_code_and_docs

    root_path = root_path.expanduser().resolve()
    filters = resolve_sync_filters(root=root_path)
    processing = processing or processing_context(svc)
    embed_by_symbol = embed_models_by_symbol(svc, scope)
    fallback_embed = str(processing.get("active_embed_model") or "unknown")
    docs_model_label = str(processing.get("docs_model_label") or "heuristic")

    discovered_code, discovered_docs = discover_code_and_docs(
        root_path,
        filters=filters,
        max_files=max_files,
    )
    code_discovered = {norm_rel(item.relative_path) for item in discovered_code}
    docs_enabled = bool(filters.get("docs_enabled")) and bool(filters.get("doc_match_globs"))
    docs_discovered = {norm_rel(item.relative_path) for item in discovered_docs} if docs_enabled else set()

    symbols = list(svc.store.list_symbols(scope))
    indexed_code: set[str] = set()
    indexed_docs: set[str] = set()
    llm_done: list[str] = []
    llm_remaining: list[str] = []
    file_meta: dict[str, dict[str, str]] = {}

    code_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"symbols": 0, "documented": 0, "embed_models": set(), "docs_models": set()}
    )
    docs_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"symbols": 0, "documented": 0, "embed_models": set(), "docs_models": set()}
    )

    for sym in symbols:
        kind = sym.kind.value if hasattr(sym.kind, "value") else str(sym.kind)
        rel = rel_under(root_path, str(sym.file_path or ""))
        if rel is None:
            continue
        sid = str(getattr(sym, "id", "") or "")
        embed_model = embed_by_symbol.get(sid) or ""

        if kind == SymbolKind.FILE.value and rel in code_discovered:
            indexed_code.add(rel)
            file_meta[rel] = {
                "hash": str(getattr(sym, "hash_value", "") or ""),
                "language": str(getattr(sym, "language", "") or ""),
                "updated_at": str(getattr(sym, "updated_at", "") or ""),
            }
            if embed_model:
                code_stats[rel]["embed_models"].add(embed_model)
        elif rel in code_discovered and kind != SymbolKind.DOCUMENTATION.value:
            indexed_code.add(rel)

        if kind == SymbolKind.DOCUMENTATION.value and rel in docs_discovered:
            indexed_docs.add(rel)
            docs_stats[rel]["symbols"] += 1
            docs_stats[rel]["documented"] += 1
            docs_stats[rel]["docs_models"].add("human")
            if embed_model:
                docs_stats[rel]["embed_models"].add(embed_model)

        if kind in CODE_KINDS and rel in code_discovered:
            status = sym.doc_status.value if hasattr(sym.doc_status, "value") else str(sym.doc_status or "")
            label = f"{rel}::{sym.qualified_name or sym.name}"
            code_stats[rel]["symbols"] += 1
            code_stats[rel]["embed_models"].add(embed_model or fallback_embed)
            if status in DOCUMENTED or (sym.ai_documentation or "").strip():
                llm_done.append(label)
                code_stats[rel]["documented"] += 1
                if status == "human":
                    code_stats[rel]["docs_models"].add("human")
                else:
                    code_stats[rel]["docs_models"].add(docs_model_label)
            else:
                llm_remaining.append(label)

    freshness = svc.freshness_status(scope) if hasattr(svc, "freshness_status") else {}
    pending_raw = [str(p) for p in (freshness.get("pending_files") or []) if str(p).strip()]
    pending_rels: set[str] = set()
    for raw in pending_raw:
        rel = rel_under(root_path, raw) or norm_rel(raw)
        if rel in code_discovered or rel in docs_discovered:
            pending_rels.add(rel)

    code_edited_map = classify_edited_paths(
        root_path=root_path,
        indexed=indexed_code,
        pending_rels=pending_rels,
        file_meta=file_meta,
    )
    # Docs: pending-only (body hash is post-frontmatter; disk compare is best-effort via pending).
    docs_edited_map = {
        rel: "pending"
        for rel in sorted(indexed_docs & pending_rels)
    }

    code_edited = set(code_edited_map)
    docs_edited = set(docs_edited_map)
    code_done = sorted(indexed_code - code_edited)
    code_edited_list = sorted(code_edited)
    code_remaining = sorted(code_discovered - indexed_code)
    docs_done = sorted(indexed_docs - docs_edited) if docs_discovered else []
    docs_edited_list = sorted(docs_edited)
    docs_remaining = sorted(docs_discovered - indexed_docs) if docs_discovered else []

    for rel in code_done + code_edited_list:
        stats = code_stats[rel]
        if not stats["embed_models"]:
            stats["embed_models"].add(fallback_embed)

    def _code_rows(paths: list[str], status: str) -> list[dict[str, Any]]:
        rows = [
            file_row(
                path=rel,
                status=status,
                symbols=int(code_stats[rel]["symbols"]),
                documented=int(code_stats[rel]["documented"]),
                embed_models=list(code_stats[rel]["embed_models"]),
                docs_models=list(code_stats[rel]["docs_models"]),
                category="code",
                edit_reason=code_edited_map.get(rel, ""),
            )
            for rel in paths
        ]
        return sort_done(rows) if status != "remaining" else sort_remaining(rows)

    def _docs_rows(paths: list[str], status: str) -> list[dict[str, Any]]:
        rows = [
            file_row(
                path=rel,
                status=status,
                symbols=int(docs_stats[rel]["symbols"]),
                documented=int(docs_stats[rel]["documented"]),
                embed_models=list(docs_stats[rel]["embed_models"]),
                docs_models=list(docs_stats[rel]["docs_models"]) or (["human"] if status != "remaining" else []),
                category="docs",
                edit_reason=docs_edited_map.get(rel, ""),
            )
            for rel in paths
        ]
        return sort_done(rows) if status != "remaining" else sort_remaining(rows)

    code_done_files = _code_rows(code_done, "done")
    code_edited_files = _code_rows(code_edited_list, "edited")
    code_remaining_files = _code_rows(code_remaining, "remaining")
    docs_done_files = _docs_rows(docs_done, "done")
    docs_edited_files = _docs_rows(docs_edited_list, "edited")
    docs_remaining_files = _docs_rows(docs_remaining, "remaining")

    models_used = sorted(
        {
            *(m for row in code_done_files for m in row.get("models") or []),
            *(m for row in code_edited_files for m in row.get("models") or []),
            *(m for row in docs_done_files for m in row.get("models") or []),
            *(m for row in docs_edited_files for m in row.get("models") or []),
        }
    )

    code_bucket = status_bucket(code_done, code_edited_list, code_remaining)
    docs_bucket = status_bucket(docs_done, docs_edited_list, docs_remaining)
    languages = language_breakdown(
        discovered_code,
        done=code_done,
        edited=code_edited_list,
        remaining=code_remaining,
    )
    code_bytes = sum(int(getattr(item, "size_bytes", 0) or 0) for item in discovered_code)
    docs_bytes = sum(int(getattr(item, "size_bytes", 0) or 0) for item in discovered_docs)

    return {
        "path": str(root_path),
        "filters": {
            "sources": filters.get("sources") or [],
            "docs_enabled": docs_enabled,
            "doc_match_globs": list(filters.get("doc_match_globs") or []),
        },
        "processing": processing,
        "models_used": models_used,
        "totals": {
            "code_files": len(discovered_code),
            "code_bytes": code_bytes,
            "docs_files": len(discovered_docs),
            "docs_bytes": docs_bytes,
        },
        "languages": languages,
        "code": {
            **code_bucket,
            "pending_count": len(pending_rels & code_discovered),
            "pending": sorted(pending_rels & code_discovered),
            "llm": bucket(llm_done, llm_remaining),
            "done_files": code_done_files,
            "edited_files": code_edited_files,
            "remaining_files": code_remaining_files,
            "top_done": top(code_done_files),
            "top_edited": top(code_edited_files),
            "top_remaining": top(code_remaining_files),
        },
        "docs": {
            **docs_bucket,
            "enabled": docs_enabled,
            "done_files": docs_done_files,
            "edited_files": docs_edited_files,
            "remaining_files": docs_remaining_files,
            "top_done": top(docs_done_files),
            "top_edited": top(docs_edited_files),
            "top_remaining": top(docs_remaining_files),
        },
    }


def build_inventory_report(
    _args: argparse.Namespace | None = None,
    *,
    roots: list[Path] | None = None,
    max_files: int | None = None,
    scope: Any | None = None,
) -> dict[str, Any]:
    svc = _graph_service()
    # Scope from identity/env/connect defaults only (inventory uses word modes, not dashed flags).
    if scope is None:
        scope = _graph_scope(
            argparse.Namespace(tenant="", workspace="", project=""),
            with_defaults=True,
        )
    if roots is None:
        roots = [Path(p) for p in require_software_paths(cli_paths=None)]
    else:
        roots = [Path(p).expanduser().resolve() for p in roots]
    if max_files is None:
        max_files = int(getattr(_args, "max_files", None) or 2000) if _args is not None else 2000
    processing = processing_context(svc)
    results = [
        inventory_one_root(
            svc=svc,
            scope=scope,
            root_path=root,
            max_files=max_files,
            processing=processing,
        )
        for root in roots
    ]

    def _sum_status(key: str) -> dict[str, int | float]:
        done = 0
        edited = 0
        remaining = 0
        for row in results:
            block = row[key]
            done += int(block.get("done_count") or 0)
            edited += int(block.get("edited_count") or 0)
            remaining += int(block.get("remaining_count") or 0)
        total = done + edited + remaining
        return {
            "done_count": done,
            "edited_count": edited,
            "remaining_count": remaining,
            "total": total,
            "percent_done": pct(done, total),
            "percent_edited": pct(edited, total),
            "percent_remaining": pct(remaining, total),
        }

    def _sum_llm() -> dict[str, int | float]:
        done = 0
        remaining = 0
        for row in results:
            block = row["code"]["llm"]
            done += int(block["done_count"])
            remaining += int(block["remaining_count"])
        total = done + remaining
        return {
            "done_count": done,
            "remaining_count": remaining,
            "total": total,
            "percent_done": pct(done, total),
        }

    models_used = sorted({m for row in results for m in (row.get("models_used") or [])})

    def _sum_totals() -> dict[str, int]:
        return {
            "code_files": sum(int((r.get("totals") or {}).get("code_files") or 0) for r in results),
            "code_bytes": sum(int((r.get("totals") or {}).get("code_bytes") or 0) for r in results),
            "docs_files": sum(int((r.get("totals") or {}).get("docs_files") or 0) for r in results),
            "docs_bytes": sum(int((r.get("totals") or {}).get("docs_bytes") or 0) for r in results),
        }

    def _merge_languages() -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "files": 0,
                "bytes": 0,
                "done_count": 0,
                "edited_count": 0,
                "remaining_count": 0,
            }
        )
        for row in results:
            for item in row.get("languages") or []:
                lang = str(item.get("language") or "unknown")
                bucket_row = merged[lang]
                for key in ("files", "bytes", "done_count", "edited_count", "remaining_count"):
                    bucket_row[key] += int(item.get(key) or 0)
        total_files = sum(int(b["files"]) for b in merged.values())
        total_bytes = sum(int(b["bytes"]) for b in merged.values())
        out: list[dict[str, Any]] = []
        for language, row in sorted(merged.items(), key=lambda kv: (-int(kv[1]["files"]), kv[0])):
            files = int(row["files"])
            nbytes = int(row["bytes"])
            out.append(
                {
                    "language": language,
                    "files": files,
                    "bytes": nbytes,
                    "percent_of_code": pct(files, total_files),
                    "percent_of_bytes": pct(nbytes, total_bytes),
                    "done_count": int(row["done_count"]),
                    "edited_count": int(row["edited_count"]),
                    "remaining_count": int(row["remaining_count"]),
                    "percent_done": pct(int(row["done_count"]), files),
                    "percent_edited": pct(int(row["edited_count"]), files),
                    "percent_remaining": pct(int(row["remaining_count"]), files),
                }
            )
        return out

    return {
        "scope": {
            "tenant": scope.tenant_id,
            "workspace": scope.workspace_id,
            "project": scope.project_id,
        },
        "paths": [r["path"] for r in results],
        "processing": processing,
        "models_used": models_used,
        "totals": _sum_totals(),
        "languages": _merge_languages(),
        "summary": {
            "code": _sum_status("code"),
            "docs": _sum_status("docs"),
            "llm": _sum_llm(),
        },
        "results": results,
    }
