"""Ingest + docs-link orchestration for a single software path."""

from __future__ import annotations

import argparse
import threading
from pathlib import Path
from typing import Any

from agentcore_cli import ui
from agentcore_cli.commands.sync.banner import print_filters_banner
from agentcore_cli.commands.sync.report import build_usage_tasks, print_sync_complete
from agentcore_cli.docs_link_sync import sync_human_docs
from agentcore_cli.sync_config import resolve_sync_filters
from agentcore_cli.sync_followup_tasks import create_sync_followup_tasks
from agentcore_cli.sync_progress import SyncProgressTracker
from agentcore_cli.sync_standards_gate import resolve_standards_gate
from agentcore_cli.sync_usage_log import TimedPhase, approx_tokens_from_chars, estimate_output_tokens
from agentcore_cli.util import now_iso


def sync_one_root(
    *,
    svc: Any,
    scope: Any,
    root_path: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    filters = resolve_sync_filters(
        root=root_path,
        cli_exclude_dirs=list(args.exclude_dir or []),
        cli_include_paths=list(args.include_path or []),
        cli_include_extensions=list(args.include_ext or []) or None,
    )
    filters = {**filters, "max_files": int(args.max_files)}
    filters, standards_gate = resolve_standards_gate(
        root_path=root_path,
        filters=filters,
        skip_nonconforming=bool(getattr(args, "skip_nonconforming", False)),
        sync_nonconforming=bool(getattr(args, "sync_nonconforming", False)),
    )
    print_filters_banner(
        scope=scope,
        root_path=root_path,
        args=args,
        filters=filters,
        standards_gate=standards_gate,
        svc=svc,
    )

    scope_txt = f"{scope.tenant_id}/{scope.workspace_id}/{scope.project_id}"
    tracker = SyncProgressTracker(
        scope=scope_txt,
        path=str(root_path),
        interval_sec=float(args.progress_interval),
    )
    session_monitor_stop = threading.Event()

    def _monitor_sessions() -> None:
        while not session_monitor_stop.is_set():
            try:
                tracker.update_sessions(svc.llm_sessions_snapshot())
            except Exception:  # noqa: BLE001
                pass
            session_monitor_stop.wait(0.1)

    session_monitor = threading.Thread(target=_monitor_sessions, daemon=True)
    session_monitor.start()
    ingest_timer = TimedPhase()
    cancelled = False
    ingest_sec = 0.0
    payload: dict[str, Any] = {}
    tokens_in = 0
    docs_payload: dict[str, Any] = {}
    docs_sec = 0.0
    docs_tokens_in = 0
    try:
        result = svc.sync_repo(
            scope,
            "cli",
            f"cli-sync-{now_iso()}",
            f"cli-sync:{root_path}",
            {
                "root_path": str(root_path),
                "include_extensions": filters["include_extensions"],
                "exclude_dirs": filters["exclude_dirs"],
                "exclude_globs": filters["exclude_globs"],
                "include_path_prefixes": filters["include_paths"],
                "max_files": int(args.max_files),
                "include_outcomes": True,
                "on_progress": tracker,
            },
        )
        ingest_sec = ingest_timer.stop()

        payload = result.to_dict() if hasattr(result, "to_dict") else result
        latest = getattr(tracker, "_latest", {}) or {}
        tokens_in = int(latest.get("approx_tokens") or 0)
        if not tokens_in:
            tokens_in = approx_tokens_from_chars(int(latest.get("chars_read") or 0))

        if filters.get("docs_enabled") and filters.get("doc_match_globs"):
            ui.blank()
            print(f"{ui.accent('→')}  Linking human documentation")
            tracker.begin_phase()
            docs_timer = TimedPhase()
            docs_result = sync_human_docs(
                graph_service=svc,
                graph_scope=scope,
                root_path=root_path,
                filters={**filters, "max_files": int(args.max_files)},
                actor="cli",
                correlation_id=f"cli-docs-{now_iso()}",
                repo_name=root_path.name,
                on_progress=tracker,
            )
            docs_sec = docs_timer.stop()
            docs_payload = docs_result.to_dict()
            docs_tokens_in = approx_tokens_from_chars(
                int(docs_payload.get("docs_indexed") or 0) * 2048
            )
            ui.kv(
                "Docs",
                f"indexed={docs_payload.get('docs_indexed')}  "
                f"links={docs_payload.get('links_created')}  "
                f"anchors={docs_payload.get('anchors_registered')}",
            )
            if docs_payload.get("evidence_enabled"):
                ui.kv(
                    "Evidence",
                    f"new_tokens={docs_payload.get('evidence_tokens_new')}  "
                    f"fm_applied={docs_payload.get('evidence_frontmatter_applied')}  "
                    f"catalog_order={docs_payload.get('catalog_ordered')}",
                )
            if docs_payload.get("unresolved_tokens"):
                ui.kv("Unresolved", ", ".join(docs_payload["unresolved_tokens"][:8]))
    except KeyboardInterrupt:
        cancelled = True
        raise
    finally:
        session_monitor_stop.set()
        session_monitor.join(timeout=1.0)
        tracker.finish(cancelled=cancelled)

    tokens_out = estimate_output_tokens(
        symbols_documented=int(payload.get("symbols_documented") or 0),
        docs_indexed=int(docs_payload.get("docs_indexed") or 0),
    )
    tasks = build_usage_tasks(
        root_path=root_path,
        payload=payload,
        docs_payload=docs_payload,
        ingest_sec=ingest_sec,
        docs_sec=docs_sec,
        tokens_in=tokens_in,
        docs_tokens_in=docs_tokens_in,
    )
    print_sync_complete(
        svc=svc,
        payload=payload,
        docs_payload=docs_payload,
        tokens_in=tokens_in,
        docs_tokens_in=docs_tokens_in,
        tokens_out=tokens_out,
        ingest_sec=ingest_sec,
        docs_sec=docs_sec,
    )

    followup: dict[str, Any] = {"ok": True, "specs_count": 0, "tasks_created_count": 0}
    try:
        followup = create_sync_followup_tasks(
            scope=scope,
            standards_gate=standards_gate,
            include_code_audit=True,
        )
        if int(followup.get("specs_count") or 0) > 0:
            ui.blank()
            ui.kv(
                "Follow-up tasks",
                (
                    f"specs={followup.get('specs_count')}  "
                    f"created={followup.get('tasks_created_count')}  "
                    f"mirror={followup.get('mirror_path')}"
                ),
            )
    except Exception as exc:  # noqa: BLE001 — never fail sync on follow-up
        followup = {"ok": False, "error": str(exc)}

    return {
        "path": str(root_path),
        "filters": {
            "sources": filters["sources"],
            "exclude_dirs_count": len(filters["exclude_dirs"]),
            "exclude_globs_count": len(filters["exclude_globs"]),
            "include_paths": filters["include_paths"],
            "include_extensions": filters["include_extensions"],
            "doc_match_globs": filters.get("doc_match_globs") or [],
            "docs_enabled": bool(filters.get("docs_enabled")),
        },
        "standards_gate": standards_gate.to_dict(),
        "followup_tasks": followup,
        "sync": payload,
        "docs_link": docs_payload,
        "_usage": {
            "duration_sec": ingest_sec + docs_sec,
            "tokens_in": tokens_in + docs_tokens_in,
            "tokens_out": tokens_out,
            "tasks": tasks,
        },
    }


# Compat alias for live tests / older imports.
_sync_one_root = sync_one_root
