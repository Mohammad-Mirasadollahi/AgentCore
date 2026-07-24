"""Repository tree walk ingest."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from .parallel_files import run_parallel_file_jobs

from ...domain.enums import RelType, SymbolKind
from ...domain.errors import ValidationError
from ...domain.hashing import digest, normalize_source
from ...domain.models import (
    RepoIngestFileOutcome,
    RepoIngestResult,
    Scope,
)
from ...domain.package_manifests import load_package_aliases
from ...domain.repo_discovery import (
    DEFAULT_MAX_FILE_BYTES,
    DEFAULT_MAX_FILES,
    discover_source_files,
)
from ...locked_store import sync_max_file_workers


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
        Files are processed with a bounded worker pool; store mutations must be
        serialized by the caller (LockedStore in bootstrap).
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
        discovered = discover_source_files(
            root_path,
            include_extensions=include_extensions,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            include_path_prefixes=include_path_prefixes,
            max_files=None,
            max_file_bytes=max_file_bytes,
        )

        indexed_files = {
            s.file_path.replace("\\", "/"): s
            for s in self.store.list_symbols(scope)
            if s.kind == SymbolKind.FILE and s.file_path and not s.file_path.startswith("__agentcore__/")
        }
        indexed_paths = set(indexed_files)
        unindexed = [d for d in discovered if d.relative_path.replace("\\", "/") not in indexed_paths]
        known = [d for d in discovered if d.relative_path.replace("\\", "/") in indexed_paths]

        def _known_changed(item: Any) -> bool:
            previous = indexed_files[item.relative_path.replace("\\", "/")]
            try:
                source = Path(item.absolute_path).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                return True
            return digest(normalize_source(source, item.language)) != previous.hash_value

        changed_known = [item for item in known if _known_changed(item)]
        changed_known_paths = {item.relative_path.replace("\\", "/") for item in changed_known}
        unchanged_known = [
            item
            for item in known
            if item.relative_path.replace("\\", "/") not in changed_known_paths
        ]
        # Prefer never-indexed files so truncated sync continues; keep a budget for re-checks.
        selected: list = []
        selected.extend(unindexed[:max_files])
        remaining = max_files - len(selected)
        if remaining > 0:
            selected.extend(changed_known[:remaining])
        remaining = max_files - len(selected)
        if remaining > 0:
            selected.extend(unchanged_known[:remaining])
        selected_paths = {item.relative_path.replace("\\", "/") for item in selected}
        pending_paths = {
            item.relative_path.replace("\\", "/") for item in [*unindexed, *changed_known]
        }
        truncated = not pending_paths.issubset(selected_paths)
        discovered = selected
        queue_new = sum(
            1
            for item in selected
            if item.relative_path.replace("\\", "/") not in indexed_paths
        )
        queue_changed = sum(
            1
            for item in selected
            if item.relative_path.replace("\\", "/") in changed_known_paths
        )
        queue_unchanged = max(0, len(selected) - queue_new - queue_changed)
        prior_indexed = len(known)
        queue_meta = {
            "prior_indexed": prior_indexed,
            "queue_new": queue_new,
            "queue_changed": queue_changed,
            "queue_unchanged": queue_unchanged,
        }

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
        # done/total = every selected file this run processes (incl. unchanged recheck).
        # Queue line still shows new/changed/unchanged_recheck separately.
        progress_total = total_files
        state_lock = threading.Lock()
        progress_done = 0
        active_files: set[str] = set()
        workers = min(sync_max_file_workers(), max(1, total_files or 1))
        shared_resolution = {
            "indexes": None,
            "by_qualified": {},
            "short_names": {},
        }
        try:
            indexes, by_qualified, short_names = self._resolution_indexes(scope)
            shared_resolution = {
                "indexes": indexes,
                "by_qualified": by_qualified,
                "short_names": short_names,
            }
        except Exception:  # noqa: BLE001 — empty graph / store ok on cold start
            pass

        def _rpm_progress_fields() -> dict[str, Any]:
            llm = getattr(self, "llm", None)
            snap_fn = getattr(llm, "rpm_sessions_snapshot", None) if llm is not None else None
            if not callable(snap_fn):
                return {}
            try:
                snap = snap_fn()
            except Exception:  # noqa: BLE001
                return {}
            return {
                "rpm": int(snap.get("rpm") or 0),
                "rpm_inflight_cap": int(snap.get("inflight_cap") or 0),
                "rpm_inflight": int(snap.get("inflight_count") or 0),
                "rpm_starts_in_window": int(snap.get("starts_in_window") or 0),
            }

        def _bump_progress(_rel: str) -> int:
            nonlocal progress_done
            progress_done += 1
            return progress_done

        def _emit(done: int, *, file: str = "", status: str = "") -> None:
            if not callable(on_progress):
                return
            try:
                with state_lock:
                    snap_totals = dict(totals)
                    in_flight_paths = sorted(active_files)
                event = {
                    "phase": "ingest",
                    "done": done,
                    "total": progress_total,
                    "file": file,
                    "status": status,
                    # done/total = all selected files this run (incl. unchanged rechecks).
                    "prior_indexed": int(queue_meta["prior_indexed"]),
                    "queue_new": int(queue_meta["queue_new"]),
                    "queue_changed": int(queue_meta["queue_changed"]),
                    "queue_unchanged": int(queue_meta["queue_unchanged"]),
                    "files_ingested": snap_totals["ingested"],
                    "files_failed": snap_totals["failed"],
                    "files_skipped": snap_totals["skipped"],
                    "symbols_indexed": snap_totals["symbols_indexed"],
                    "symbols_changed": snap_totals["symbols_changed"],
                    "edges_written": snap_totals["edges_written"],
                    "chars_read": snap_totals["chars_read"],
                    "approx_tokens": snap_totals["chars_read"] // 4,
                    "files_in_flight": len(in_flight_paths),
                    "files_in_flight_paths": in_flight_paths[:8],
                    "file_workers": workers,
                }
                event.update(_rpm_progress_fields())
                on_progress(event)
            except Exception:  # noqa: BLE001 — progress must never break ingest
                return

        def _process_one(index: int, item: Any) -> None:
            rel = item.relative_path
            with state_lock:
                active_files.add(rel)
                done_now = progress_done
            _emit(done_now, file=rel, status="active")
            try:
                text = Path(item.absolute_path).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                with state_lock:
                    totals["skipped"] += 1
                    done = _bump_progress(rel)
                    active_files.discard(rel)
                    if include_outcomes:
                        outcomes.append(
                            RepoIngestFileOutcome(
                                relative_path=rel,
                                language=item.language,
                                status="skipped",
                                detail="not_utf8",
                            )
                        )
                _emit(done, file=rel, status="skipped")
                return
            except OSError as exc:
                with state_lock:
                    totals["failed"] += 1
                    done = _bump_progress(rel)
                    active_files.discard(rel)
                    if include_outcomes:
                        outcomes.append(
                            RepoIngestFileOutcome(
                                relative_path=rel,
                                language=item.language,
                                status="failed",
                                detail=f"read_error:{exc}",
                            )
                        )
                _emit(done, file=rel, status="failed")
                return

            file_key = f"{idempotency_key}:{rel}:{index}"
            try:
                result = self.ingest_file(
                    scope,
                    actor_id,
                    correlation_id,
                    file_key,
                    {
                        "file_path": rel,
                        "source": text,
                        "language": item.language,
                        "package_aliases": package_aliases,
                        "defer_cross_file_pass": True,
                        "shared_resolution": shared_resolution,
                    },
                )
            except Exception as exc:  # noqa: BLE001 — soft-fail per file for bulk jobs
                with state_lock:
                    totals["failed"] += 1
                    done = _bump_progress(rel)
                    active_files.discard(rel)
                    if include_outcomes:
                        outcomes.append(
                            RepoIngestFileOutcome(
                                relative_path=rel,
                                language=item.language,
                                status="failed",
                                detail=str(exc)[:500],
                            )
                        )
                _emit(done, file=rel, status="failed")
                return

            unchanged = (
                result.symbols_indexed == 0
                and result.symbols_changed == 0
                and result.edges_written == 0
            )
            with state_lock:
                if unchanged:
                    totals["skipped"] += 1
                else:
                    totals["ingested"] += 1
                totals["chars_read"] += len(text)
                totals["symbols_indexed"] += result.symbols_indexed
                totals["symbols_changed"] += result.symbols_changed
                totals["symbols_documented"] += result.symbols_documented
                totals["edges_written"] += result.edges_written
                done = _bump_progress(rel)
                active_files.discard(rel)
                if include_outcomes:
                    outcomes.append(
                        RepoIngestFileOutcome(
                            relative_path=rel,
                            language=item.language,
                            status="unchanged" if unchanged else "ok",
                            file_id=result.file_id,
                            symbols_indexed=result.symbols_indexed,
                            symbols_changed=result.symbols_changed,
                            symbols_documented=result.symbols_documented,
                            edges_written=result.edges_written,
                        )
                    )
            _emit(done, file=rel, status="unchanged" if unchanged else "ok")

        _emit(0, status="started")
        if total_files:
            run_parallel_file_jobs(workers=workers, items=discovered, fn=_process_one)

        try:
            finals = self.finalize_cross_file_resolution(
                scope,
                package_aliases=package_aliases,
            )
            with state_lock:
                totals["edges_written"] += int(finals or 0)
        except Exception:  # noqa: BLE001 — finalize must not fail the ingest walk
            pass

        _emit(progress_total, status="finished")

        resolved_root = str(Path(root_path).expanduser().resolve())
        try:
            readme_edges = self._ingest_package_readme_maps(scope, resolved_root)
            totals["edges_written"] += readme_edges
        except Exception:  # noqa: BLE001 — package README ingest must not fail the repo walk
            readme_edges = 0

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

    def _ingest_package_readme_maps(self, scope: Scope, root_path: str) -> int:
        """Index near-code package README maps as human DOCUMENTATION + DOCUMENTED_BY from FILEs."""
        root = Path(root_path)
        if not root.is_dir():
            return 0
        skip_parts = {
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "__pycache__",
            "dist",
            "build",
            "vendor",
            ".tox",
        }
        upsert = getattr(self, "upsert_human_documentation", None)
        put_edge = getattr(self, "_put_edge", None)
        if not callable(upsert) or not callable(put_edge):
            return 0

        edges = 0
        for readme in root.rglob("README.md"):
            try:
                rel = readme.relative_to(root).as_posix()
            except ValueError:
                continue
            if set(rel.split("/")) & skip_parts:
                continue
            parent = readme.parent
            has_code = (
                any(parent.glob("*.py"))
                or any(parent.glob("*.ts"))
                or any(parent.glob("*.tsx"))
                or any(parent.glob("*.js"))
                or any(parent.glob("*.go"))
                or any(parent.glob("*.rs"))
            )
            if not has_code:
                continue
            try:
                body = readme.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if len(body.strip()) < 40:
                continue
            doc_id = f"package-readme:{rel}"
            result = upsert(
                scope,
                doc_id=doc_id,
                relative_path=rel,
                body=body[:8000],
                title=f"Package map: {parent.name}",
                linked_symbol_tokens=[],
                metadata={"origin": "package_readme", "provenance": "package_folder_readme"},
            )
            dir_prefix = str(Path(rel).parent).replace("\\", "/")
            if dir_prefix in {".", ""}:
                dir_prefix = ""
            doc_sid = str(result.get("doc_symbol_id") or "")
            if not doc_sid:
                continue
            for sym in self.store.list_symbols(scope):
                if sym.kind != SymbolKind.FILE:
                    continue
                fp = (sym.file_path or "").replace("\\", "/")
                parent_dir = str(Path(fp).parent).replace("\\", "/")
                if parent_dir in {".", ""}:
                    parent_dir = ""
                if parent_dir != dir_prefix:
                    continue
                edges += put_edge(
                    scope,
                    RelType.DOCUMENTED_BY.value,
                    sym.id,
                    doc_sid,
                    file_path=fp,
                    metadata={"doc_id": doc_id, "origin": "package_readme"},
                    link_key=f"package_readme:{doc_id}:{sym.id}",
                )
        return edges
