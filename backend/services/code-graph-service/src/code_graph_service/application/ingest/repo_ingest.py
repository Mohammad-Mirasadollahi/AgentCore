"""Repository tree walk ingest."""

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

class RepoIngestMixin:
    """Bulk ingest via discover_source_files + ingest_file."""

    def ingest_repo(
        self,
        scope: Scope,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> RepoIngestResult:
        """Walk a repository root and ingest every supported source file.

        Reuses ``ingest_file`` per file. Failures are collected; the walk continues.
        """
        root_path = str(payload.get("root_path") or "").strip()
        if not root_path:
            raise ValidationError("root_path is required")

        include_extensions = payload.get("include_extensions")
        exclude_dirs = payload.get("exclude_dirs")
        exclude_globs = payload.get("exclude_globs")
        include_path_prefixes = payload.get("include_path_prefixes") or payload.get("include_paths")
        max_files = int(payload.get("max_files") or DEFAULT_MAX_FILES)
        max_file_bytes = int(payload.get("max_file_bytes") or DEFAULT_MAX_FILE_BYTES)
        include_outcomes = bool(payload.get("include_outcomes", True))
        # Probe one extra so we can report truncation without a second walk.
        probe_limit = max_files + 1 if max_files < 20_000 else max_files
        discovered = discover_source_files(
            root_path,
            include_extensions=include_extensions,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            include_path_prefixes=include_path_prefixes,
            max_files=probe_limit,
            max_file_bytes=max_file_bytes,
        )
        truncated = len(discovered) > max_files
        if truncated:
            discovered = discovered[:max_files]

        package_aliases = load_package_aliases(root_path)

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
        on_progress = payload.get("on_progress")
        total_files = len(discovered)

        def _emit(done: int, *, file: str = "", status: str = "") -> None:
            if not callable(on_progress):
                return
            try:
                on_progress(
                    {
                        "phase": "ingest",
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
            except Exception:  # noqa: BLE001 — progress must never break ingest
                return

        _emit(0, status="started")

        for index, item in enumerate(discovered):
            try:
                text = Path(item.absolute_path).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                totals["skipped"] += 1
                if include_outcomes:
                    outcomes.append(
                        RepoIngestFileOutcome(
                            relative_path=item.relative_path,
                            language=item.language,
                            status="skipped",
                            detail="not_utf8",
                        )
                    )
                _emit(index + 1, file=item.relative_path, status="skipped")
                continue
            except OSError as exc:
                totals["failed"] += 1
                if include_outcomes:
                    outcomes.append(
                        RepoIngestFileOutcome(
                            relative_path=item.relative_path,
                            language=item.language,
                            status="failed",
                            detail=f"read_error:{exc}",
                        )
                    )
                _emit(index + 1, file=item.relative_path, status="failed")
                continue

            file_key = f"{idempotency_key}:{item.relative_path}:{index}"
            try:
                result = self.ingest_file(
                    scope,
                    actor_id,
                    correlation_id,
                    file_key,
                    {
                        "file_path": item.relative_path,
                        "source": text,
                        "language": item.language,
                        "package_aliases": package_aliases,
                    },
                )
            except Exception as exc:  # noqa: BLE001 — soft-fail per file for bulk jobs
                totals["failed"] += 1
                if include_outcomes:
                    outcomes.append(
                        RepoIngestFileOutcome(
                            relative_path=item.relative_path,
                            language=item.language,
                            status="failed",
                            detail=str(exc)[:500],
                        )
                    )
                _emit(index + 1, file=item.relative_path, status="failed")
                continue

            totals["ingested"] += 1
            totals["chars_read"] += len(text)
            totals["symbols_indexed"] += result.symbols_indexed
            totals["symbols_changed"] += result.symbols_changed
            totals["symbols_documented"] += result.symbols_documented
            totals["edges_written"] += result.edges_written
            if include_outcomes:
                outcomes.append(
                    RepoIngestFileOutcome(
                        relative_path=item.relative_path,
                        language=item.language,
                        status="ok",
                        file_id=result.file_id,
                        symbols_indexed=result.symbols_indexed,
                        symbols_changed=result.symbols_changed,
                        symbols_documented=result.symbols_documented,
                        edges_written=result.edges_written,
                    )
                )
            _emit(index + 1, file=item.relative_path, status="ok")

        _emit(total_files, status="finished")

        resolved_root = str(Path(root_path).expanduser().resolve())
        return RepoIngestResult(
            root_path=resolved_root,
            files_discovered=len(discovered),
            files_ingested=totals["ingested"],
            files_failed=totals["failed"],
            files_skipped=totals["skipped"],
            symbols_indexed=totals["symbols_indexed"],
            symbols_changed=totals["symbols_changed"],
            symbols_documented=totals["symbols_documented"],
            edges_written=totals["edges_written"],
            truncated=truncated,
            outcomes=outcomes,
        )
