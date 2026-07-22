"""Phase-2 human documentation sync: docs-sync SoT + code-graph DOCUMENTED_BY projection."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentcore_cli.markdown_frontmatter import parse_markdown_frontmatter, provisional_frontmatter
from agentcore_cli.util import repo_root


@dataclass
class DocsLinkSyncResult:
    docs_discovered: int = 0
    docs_indexed: int = 0
    anchors_registered: int = 0
    links_created: int = 0
    unresolved_tokens: list[str] = field(default_factory=list)
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "docs_discovered": self.docs_discovered,
            "docs_indexed": self.docs_indexed,
            "anchors_registered": self.anchors_registered,
            "links_created": self.links_created,
            "unresolved_tokens": list(self.unresolved_tokens),
            "skipped": self.skipped,
            "errors": list(self.errors),
        }


def _ensure_docs_sync_import() -> None:
    root = repo_root()
    src = root / "backend" / "services" / "docs-sync-service" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _docs_sync_service():
    """In-process docs-sync (Postgres when URL set; else memory)."""
    from agentcore_cli.cli_defaults import load_dotenv_files

    load_dotenv_files()
    _ensure_docs_sync_import()
    url = os.environ.get("AGENTCORE_DOCS_SYNC_DATABASE_URL", "").strip()
    if url.startswith(("postgresql://", "postgresql+psycopg://")):
        from docs_sync_service.bootstrap import Settings, build_service

        return build_service(Settings(database_url=url))
    from docs_sync_service.core import DocsSyncService
    from docs_sync_service.testing import InMemoryStore

    return DocsSyncService(InMemoryStore())


def sync_human_docs(
    *,
    graph_service: Any,
    graph_scope: Any,
    root_path: Path,
    filters: dict[str, Any],
    actor: str = "cli",
    correlation_id: str = "",
    repo_name: str = "repo",
) -> DocsLinkSyncResult:
    """Discover Markdown via docs.match globs, index in docs-sync, project edges."""
    from code_graph_service.domain.doc_discovery import discover_documentation_files
    from code_graph_service.domain.hashing import digest

    _ensure_docs_sync_import()
    from docs_sync_service.core import Scope as DocsScope

    result = DocsLinkSyncResult()
    if not filters.get("docs_enabled", True):
        return result
    match_globs = list(filters.get("doc_match_globs") or [])
    if not match_globs:
        return result

    root_path = root_path.expanduser().resolve()
    discovered = discover_documentation_files(
        root_path,
        match_globs=match_globs,
        exclude_dirs=filters.get("doc_exclude_dirs"),
        exclude_globs=filters.get("doc_exclude_globs"),
        doc_paths=filters.get("doc_paths") or None,
        max_files=int(filters.get("max_files") or 2000),
    )
    result.docs_discovered = len(discovered)
    if not discovered:
        return result

    docs_svc = _docs_sync_service()
    docs_scope = DocsScope(
        graph_scope.tenant_id,
        graph_scope.workspace_id,
        graph_scope.project_id,
    )
    corr = correlation_id or f"docs-link-{graph_scope.project_id}"

    for item in discovered:
        abs_path = Path(item.absolute_path)
        rel = item.relative_path
        try:
            text = abs_path.read_text(encoding="utf-8")
        except OSError as exc:
            result.skipped += 1
            result.errors.append(f"{rel}: read failed: {exc}")
            continue

        partial, body = parse_markdown_frontmatter(text)
        frontmatter = provisional_frontmatter(rel, body, partial)
        doc_id = str(frontmatter["doc_id"]).strip()
        linked_tokens = [str(t).strip() for t in (frontmatter.get("linked_symbols") or []) if str(t).strip()]
        # Include content fingerprint so edits get a new key (same key + new body = ConflictError).
        doc_fp = digest(f"{rel}\n{doc_id}\n{linked_tokens}\n{body}")[:16]

        try:
            document = docs_svc.index_document(
                docs_scope,
                actor,
                corr,
                f"docs-index:{rel}:{doc_id}:{doc_fp}",
                {"path": rel, "frontmatter": frontmatter, "body": body},
            )
            result.docs_indexed += 1
        except Exception as exc:
            result.skipped += 1
            result.errors.append(f"{rel}: docs-sync index failed: {exc}")
            continue

        projection = graph_service.upsert_human_documentation(
            graph_scope,
            doc_id=doc_id,
            relative_path=rel,
            body=body,
            title=str(frontmatter.get("title") or doc_id),
            linked_symbol_tokens=linked_tokens,
        )
        result.links_created += int(projection.get("edges_written") or 0)
        for token in projection.get("unresolved_tokens") or []:
            if token not in result.unresolved_tokens:
                result.unresolved_tokens.append(token)

        for symbol_graph_id in projection.get("linked_symbol_ids") or []:
            try:
                graph_sym = graph_service.store.get_symbol(symbol_graph_id, graph_scope)
            except Exception:
                continue
            try:
                sym_fp = digest(
                    f"{graph_sym.qualified_name}\n{graph_sym.hash_value}\n{graph_sym.body or ''}"
                )[:16]
                ds_symbol = docs_svc.index_symbol(
                    docs_scope,
                    actor,
                    corr,
                    f"docs-sym:{symbol_graph_id}:{sym_fp}",
                    {
                        "repo": repo_name,
                        "file_path": graph_sym.file_path,
                        "symbol_path": graph_sym.qualified_name,
                        "kind": graph_sym.kind.value if hasattr(graph_sym.kind, "value") else str(graph_sym.kind),
                        "body": graph_sym.body or graph_sym.signature or graph_sym.qualified_name,
                        "signature": graph_sym.signature or graph_sym.qualified_name,
                        "doc_required": True,
                        "tags": [],
                    },
                )
                docs_svc.register_anchor(
                    docs_scope,
                    actor,
                    corr,
                    f"docs-anchor:{doc_id}:{ds_symbol.id}:{graph_sym.hash_value[:16]}",
                    {
                        "doc_id": document.id,
                        "symbol_id": ds_symbol.id,
                        "recorded_hash": graph_sym.hash_value,
                    },
                )
                result.anchors_registered += 1
            except Exception as exc:
                result.errors.append(f"{rel}: anchor failed for {symbol_graph_id}: {exc}")

    return result
