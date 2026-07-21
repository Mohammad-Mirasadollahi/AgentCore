"""Auto sync policy and purge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...domain.cross_language import (
    build_symbol_indexes,
    resolve_call_target_polyglot,
    resolve_import_target,
)
from ...domain.package_manifests import load_package_aliases
from ...domain.dispatch_synth import synthesize_interface_dispatch
from ...domain.enums import CallConfidence, DocStatus, RelType, SymbolKind
from ...domain.errors import ValidationError
from ...domain.framework_routes import extract_routes, route_symbol_id
from ...domain.freshness import extract_rationale_comments
from ...domain.hashing import digest, normalize_source, now_iso
from ...domain.languages import assert_language_supported, detect_language_from_path
from ...domain.models import (
    GraphSymbol,
    IngestResult,
    RepoIngestFileOutcome,
    RepoIngestResult,
    Scope,
    SyncRepoResult,
)
from ...domain.parsers import parse_source
from ...domain.repo_discovery import (
    DEFAULT_MAX_FILE_BYTES,
    DEFAULT_MAX_FILES,
    discover_source_files,
)
from ...domain.test_links import suggest_test_links
from ..support import GraphServiceSupport, unresolved_call_name, unresolved_symbol_id

class SyncMixin:
    """Operator-facing sync_repo / purge_scope."""

    def sync_repo(
        self,
        scope: Scope,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> SyncRepoResult:
        """Auto-choose full vs incremental sync; callers never pick a mode."""
        root_path = str(payload.get("root_path") or "").strip()
        if not root_path:
            raise ValidationError("root_path is required")
        resolved_root = Path(root_path).expanduser().resolve()
        if not resolved_root.is_dir():
            raise ValidationError(f"root_path is not a directory: {resolved_root}")

        symbols = list(self.store.list_symbols(scope))
        freshness = self.freshness_status() if hasattr(self, "freshness_status") else {"pending_files": []}
        pending = [str(p) for p in (freshness.get("pending_files") or []) if str(p).strip()]

        ingest_payload = dict(payload)
        ingest_payload["root_path"] = str(resolved_root)

        if not symbols:
            ingest = self.ingest_repo(scope, actor_id, correlation_id, idempotency_key, ingest_payload)
            hint = ""
            if ingest.truncated:
                hint = "truncated: run sync again to continue indexing more files"
            return SyncRepoResult.from_ingest(
                mode="full",
                ingest=ingest,
                freshness=self.freshness_status() if hasattr(self, "freshness_status") else freshness,
                hint=hint,
            )

        if pending:
            ingest = self._ingest_pending_paths(
                scope,
                actor_id,
                correlation_id,
                idempotency_key,
                root=resolved_root,
                pending_paths=pending,
                include_outcomes=bool(payload.get("include_outcomes", True)),
                on_progress=payload.get("on_progress"),
            )
            hint = ""
            if ingest.files_ingested == 0 and ingest.files_failed == 0:
                return SyncRepoResult.from_ingest(
                    mode="noop",
                    ingest=ingest,
                    freshness=self.freshness_status() if hasattr(self, "freshness_status") else freshness,
                    hint="no pending files could be resolved under root_path",
                )
            return SyncRepoResult.from_ingest(
                mode="incremental",
                ingest=ingest,
                freshness=self.freshness_status() if hasattr(self, "freshness_status") else freshness,
                hint=hint,
            )

        ingest = self.ingest_repo(scope, actor_id, correlation_id, idempotency_key, ingest_payload)
        mode = "noop" if ingest.files_discovered == 0 else "incremental"
        hint = ""
        if ingest.truncated:
            hint = "truncated: run sync again to continue indexing more files"
        elif mode == "noop":
            hint = "up to date (no source files discovered)"
        return SyncRepoResult.from_ingest(
            mode=mode,
            ingest=ingest,
            freshness=self.freshness_status() if hasattr(self, "freshness_status") else freshness,
            hint=hint,
        )

    def _ingest_pending_paths(
        self,
        scope: Scope,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        *,
        root: Path,
        pending_paths: list[str],
        include_outcomes: bool,
        on_progress: Any = None,
    ) -> RepoIngestResult:
        package_aliases = load_package_aliases(root)
        outcomes: list[RepoIngestFileOutcome] = []
        totals = {
            "ingested": 0,
            "failed": 0,
            "skipped": 0,
            "symbols_indexed": 0,
            "symbols_changed": 0,
            "symbols_documented": 0,
            "edges_written": 0,
            "chars_read": 0,
        }
        total_files = len(pending_paths)

        def _emit(done: int, *, file: str = "", status: str = "") -> None:
            if not callable(on_progress):
                return
            try:
                on_progress(
                    {
                        "phase": "incremental",
                        "done": done,
                        "total": total_files,
                        "file": file,
                        "status": status,
                        "files_ingested": totals["ingested"],
                        "files_failed": totals["failed"],
                        "files_skipped": totals["skipped"],
                        "symbols_indexed": totals["symbols_indexed"],
                        "symbols_changed": totals["symbols_changed"],
                        "edges_written": totals["edges_written"],
                        "chars_read": totals["chars_read"],
                        "approx_tokens": totals["chars_read"] // 4,
                    }
                )
            except Exception:  # noqa: BLE001
                return

        _emit(0, status="started")
        for index, raw in enumerate(pending_paths):
            rel, abs_path = self._resolve_pending_path(root, raw)
            if abs_path is None or not abs_path.is_file():
                totals["skipped"] += 1
                if include_outcomes:
                    outcomes.append(
                        RepoIngestFileOutcome(
                            relative_path=rel or raw,
                            language="",
                            status="skipped",
                            detail="not_found_under_root",
                        )
                    )
                _emit(index + 1, file=rel or raw, status="skipped")
                continue
            try:
                language = detect_language_from_path(str(abs_path)) or ""
            except Exception:
                language = ""
            if not language:
                totals["skipped"] += 1
                if include_outcomes:
                    outcomes.append(
                        RepoIngestFileOutcome(
                            relative_path=rel,
                            language="",
                            status="skipped",
                            detail="unsupported_language",
                        )
                    )
                if hasattr(self, "clear_pending_sync"):
                    self.clear_pending_sync(raw)
                _emit(index + 1, file=rel, status="skipped")
                continue
            try:
                text_body = abs_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                totals["failed"] += 1
                if include_outcomes:
                    outcomes.append(
                        RepoIngestFileOutcome(
                            relative_path=rel,
                            language=language,
                            status="failed",
                            detail=str(exc)[:500],
                        )
                    )
                _emit(index + 1, file=rel, status="failed")
                continue
            file_key = f"{idempotency_key}:pending:{rel}:{index}"
            try:
                result = self.ingest_file(
                    scope,
                    actor_id,
                    correlation_id,
                    file_key,
                    {
                        "file_path": rel,
                        "source": text_body,
                        "language": language,
                        "package_aliases": package_aliases,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                totals["failed"] += 1
                if include_outcomes:
                    outcomes.append(
                        RepoIngestFileOutcome(
                            relative_path=rel,
                            language=language,
                            status="failed",
                            detail=str(exc)[:500],
                        )
                    )
                _emit(index + 1, file=rel, status="failed")
                continue
            totals["ingested"] += 1
            totals["chars_read"] += len(text_body)
            totals["symbols_indexed"] += result.symbols_indexed
            totals["symbols_changed"] += result.symbols_changed
            totals["symbols_documented"] += result.symbols_documented
            totals["edges_written"] += result.edges_written
            if include_outcomes:
                outcomes.append(
                    RepoIngestFileOutcome(
                        relative_path=rel,
                        language=language,
                        status="ok",
                        file_id=result.file_id,
                        symbols_indexed=result.symbols_indexed,
                        symbols_changed=result.symbols_changed,
                        symbols_documented=result.symbols_documented,
                        edges_written=result.edges_written,
                    )
                )
            _emit(index + 1, file=rel, status="ok")
        _emit(total_files, status="finished")
        return RepoIngestResult(
            root_path=str(root),
            files_discovered=len(pending_paths),
            files_ingested=totals["ingested"],
            files_failed=totals["failed"],
            files_skipped=totals["skipped"],
            symbols_indexed=totals["symbols_indexed"],
            symbols_changed=totals["symbols_changed"],
            symbols_documented=totals["symbols_documented"],
            edges_written=totals["edges_written"],
            truncated=False,
            outcomes=outcomes,
        )

    @staticmethod
    def _resolve_pending_path(root: Path, raw: str) -> tuple[str, Path | None]:
        cleaned = (raw or "").strip().replace("\\", "/")
        if not cleaned:
            return "", None
        candidate = Path(cleaned)
        if candidate.is_absolute():
            try:
                rel = str(candidate.resolve().relative_to(root)).replace("\\", "/")
            except ValueError:
                return cleaned, None
            return rel, (root / rel)
        rel = cleaned.lstrip("./")
        return rel, (root / rel)

    def purge_scope(self, scope: Scope) -> dict[str, Any]:
        """Wipe all graph data for the project scope (embeddings + store + pending)."""
        before = len(self.store.list_symbols(scope))
        edges_before = len(self.store.list_edges(scope))
        for symbol in self.store.list_symbols(scope):
            self._delete_embedding(scope, symbol.id)
        wipe = getattr(self.store, "wipe_scope", None)
        if not callable(wipe):
            raise ValidationError("store does not support wipe_scope")
        deleted = wipe(scope)
        index_wipe = getattr(self.embedding_index, "wipe_scope", None) if self.embedding_index else None
        embeddings_deleted = 0
        if callable(index_wipe):
            embeddings_deleted = int(index_wipe(scope) or 0)
        if hasattr(self, "clear_pending_sync"):
            self.clear_pending_sync()
        return {
            "ok": True,
            "symbols_before": before,
            "edges_before": edges_before,
            "deleted": deleted,
            "embeddings_deleted": embeddings_deleted,
            "symbols_after": len(self.store.list_symbols(scope)),
            "edges_after": len(self.store.list_edges(scope)),
        }

