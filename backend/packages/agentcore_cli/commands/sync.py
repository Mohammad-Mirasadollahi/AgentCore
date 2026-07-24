"""User-facing code sync and purge (auto full vs incremental)."""

from __future__ import annotations

import argparse
import threading
from pathlib import Path
from typing import Any

from agentcore_cli import ui
from agentcore_cli.commands.graph import _graph_scope, _graph_service, _require_cloud_llm_consent
from agentcore_cli.docs_link_sync import sync_human_docs
from agentcore_cli.software_paths import require_software_paths
from agentcore_cli.sync_config import resolve_sync_filters
from agentcore_cli.sync_progress import SyncProgressTracker
from agentcore_cli.sync_standards_gate import resolve_standards_gate
from agentcore_cli.sync_followup_tasks import create_sync_followup_tasks
from agentcore_cli.sync_usage_log import (
    TimedPhase,
    append_sync_usage_record,
    approx_tokens_from_chars,
    build_sync_usage_record,
    estimate_output_tokens,
    execution_at_now,
    task_entry,
)
from agentcore_cli.util import now_iso, print_json


def _sync_one_root(
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
    scope_txt = f"{scope.tenant_id}/{scope.workspace_id}/{scope.project_id}"
    ui.blank()
    print(f"{ui.accent('→')}  Syncing {ui.scope_line(scope.tenant_id, scope.workspace_id, scope.project_id)}")
    ui.kv("Path", str(root_path))
    ui.kv("Progress", f"updates about every {int(args.progress_interval)}s (adapts ETA from observed rate)")
    if standards_gate.docs_nonconforming or standards_gate.code_nonconforming:
        ui.kv(
            "Standards gate",
            (
                f"skipped={standards_gate.skipped}  "
                f"docs_bad={len(standards_gate.docs_nonconforming)}  "
                f"docs_excluded={len(standards_gate.skipped_docs)}  "
                f"code_excluded={len(standards_gate.skipped_code)}"
            ),
        )
    rpm_snap: dict[str, Any] = {}
    try:
        if hasattr(svc, "llm_sessions_snapshot"):
            rpm_snap = svc.llm_sessions_snapshot() or {}
    except Exception:  # noqa: BLE001
        rpm_snap = {}
    rpm_limit = int(rpm_snap.get("rpm") or 0)
    try:
        from code_graph_service.locked_store import resolve_sync_cpu_plan

        plan = resolve_sync_cpu_plan()
        if plan.mode == "percent":
            ui.kv(
                "CPU budget",
                f"{plan.cpu_percent}% of {plan.cpu_count} CPUs → "
                f"{plan.workers} workers, {plan.embed_concurrency} embeds, "
                f"torch/OMP={plan.torch_threads}",
            )
        elif plan.mode == "workers":
            ui.kv(
                "CPU budget",
                f"explicit {plan.workers} workers "
                f"(embeds={plan.embed_concurrency}, torch/OMP={plan.torch_threads})",
            )
        else:
            ui.kv(
                "CPU budget",
                f"auto → {plan.workers} workers "
                f"(embeds≤{plan.embed_concurrency}, torch/OMP={plan.torch_threads}; "
                f"CPU×RPM)",
            )
    except Exception:  # noqa: BLE001
        pass
    if rpm_limit:
        ui.kv(
            "RPM",
            f"{rpm_limit} req/min  "
            f"(inflight cap {int(rpm_snap.get('inflight_cap') or rpm_limit)}; "
            f"live lines show active/starts)",
        )
    ui.kv("Config", ", ".join(filters["sources"]))
    if filters["include_paths"]:
        ui.kv("Only (legacy)", ", ".join(filters["include_paths"]))
    if filters.get("docs_enabled") and filters.get("doc_match_globs"):
        ui.kv("Docs match", ", ".join(filters["doc_match_globs"][:4]))
    n_dirs = len(filters["exclude_dirs"])
    n_globs = len(filters["exclude_globs"])
    sample = [d for d in filters["exclude_dirs"] if d not in {".git", "git"}][:4]
    sample_g = list(filters["exclude_globs"])[:3]
    bits = [f"{n_dirs} dirs"]
    if sample:
        bits.append(f"e.g. {', '.join(sample)}")
    bits.append(f"{n_globs} globs")
    if sample_g:
        bits.append(f"e.g. {', '.join(sample_g)}")
    ui.kv("Code exclude", " · ".join(bits))
    ui.blank()

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

    tasks: list[dict[str, Any]] = [
        task_entry(
            name=f"code_sync:{root_path}",
            duration_sec=ingest_sec,
            tokens_in=tokens_in,
            tokens_out=estimate_output_tokens(
                symbols_documented=int(payload.get("symbols_documented") or 0),
            ),
        )
    ]
    if docs_payload:
        tasks.append(
            task_entry(
                name=f"docs_link:{root_path}",
                duration_sec=docs_sec,
                tokens_in=docs_tokens_in,
                tokens_out=estimate_output_tokens(
                    symbols_documented=0,
                    docs_indexed=int(docs_payload.get("docs_indexed") or 0),
                ),
            )
        )

    # Per-file rows (duration share by symbols_indexed)
    outcomes = list(payload.get("outcomes") or [])
    sym_total = sum(int(o.get("symbols_indexed") or 0) for o in outcomes) or 1
    for item in outcomes:
        share = int(item.get("symbols_indexed") or 0) / sym_total
        file_in = int(tokens_in * share)
        file_out = estimate_output_tokens(
            symbols_documented=int(item.get("symbols_documented") or 0),
        )
        tasks.append(
            task_entry(
                name=f"file:{item.get('relative_path') or item.get('file_id') or '?'}",
                duration_sec=ingest_sec * share,
                tokens_in=file_in,
                tokens_out=file_out,
                extra={
                    "status": item.get("status"),
                    "language": item.get("language"),
                    "symbols_indexed": item.get("symbols_indexed"),
                },
            )
        )

    ui.blank()
    ui.heading("Sync complete")
    ui.blank()
    ui.kv("Mode", str(payload.get("mode")))
    ui.kv("Truncated", str(payload.get("truncated")))
    ui.kv("Files", f"ingested={payload.get('files_ingested')}  discovered={payload.get('files_discovered')}")
    ui.kv("Symbols", f"indexed={payload.get('symbols_indexed')}  changed={payload.get('symbols_changed')}")
    try:
        final_rpm = svc.llm_sessions_snapshot() if hasattr(svc, "llm_sessions_snapshot") else {}
    except Exception:  # noqa: BLE001
        final_rpm = {}
    if final_rpm.get("rpm"):
        ui.kv(
            "RPM final",
            f"inflight {int(final_rpm.get('inflight_count') or 0)}/"
            f"{int(final_rpm.get('inflight_cap') or final_rpm.get('rpm') or 0)}  "
            f"starts {int(final_rpm.get('starts_in_window') or 0)}/{int(final_rpm.get('rpm') or 0)}  "
            f"history {len(final_rpm.get('history') or [])}",
        )
    ui.kv(
        "Tokens≈",
        f"in={tokens_in + docs_tokens_in}  out={tokens_out}  "
        f"total={tokens_in + docs_tokens_in + tokens_out}  "
        f"({ingest_sec + docs_sec:.1f}s)",
    )
    if payload.get("hint"):
        ui.blank()
        ui.section("Hint")
        ui.bullet(str(payload["hint"]))

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


def cmd_sync(args: argparse.Namespace) -> int:
    try:
        return _cmd_sync_body(args)
    except KeyboardInterrupt:
        ui.blank()
        print(f"{ui.warn('!')} Sync stopped — graceful shutdown complete", flush=True)
        ui.blank()
        return 130


def _cmd_sync_body(args: argparse.Namespace) -> int:
    import os

    from agentcore_cli.service_runtime import ensure_running_or_offer_start
    from agentcore_cli.util import repo_root
    from code_graph_service.locked_store import apply_sync_compute_limits, resolve_sync_cpu_plan

    cpu_percent = getattr(args, "cpu_percent", None)
    if cpu_percent is not None and str(cpu_percent).strip() != "":
        os.environ["AGENTCORE_SYNC_CPU_PERCENT"] = str(cpu_percent).strip()
    apply_sync_compute_limits(resolve_sync_cpu_plan())

    started = ensure_running_or_offer_start(repo_root())
    if started is not None:
        ui.blank()
        ui.heading("AgentCore is up")
        compose = started.get("compose") or {}
        service_times = compose.get("service_started_at") or {}
        for name in compose.get("services") or []:
            ts = service_times.get(name) or compose.get("started_at") or "?"
            ui.kv(str(name), f"started at {ts}")
        mcp = started.get("mcp") or {}
        mcp_ts = mcp.get("started_at") or "?"
        mcp_bits = [f"started at {mcp_ts}"]
        if mcp.get("pid"):
            mcp_bits.append(f"pid {mcp.get('pid')}")
        if mcp.get("host") is not None and mcp.get("port") is not None:
            mcp_bits.append(f"{mcp.get('host')}:{mcp.get('port')}")
        ui.kv("MCP HTTP", "  ".join(mcp_bits))
        ui.blank()

    svc = _graph_service()
    scope = _graph_scope(args, with_defaults=True)
    scope_txt = f"{scope.tenant_id}/{scope.workspace_id}/{scope.project_id}"
    cli_paths = list(args.path) if args.path else None
    roots = [Path(p) for p in require_software_paths(cli_paths=cli_paths)]

    from agentcore_cli.commands.inventory.collect import build_inventory_report
    from agentcore_cli.commands.stats.render import print_sync_preflight

    print_sync_preflight(
        build_inventory_report(
            args,
            roots=roots,
            max_files=int(args.max_files),
            scope=scope,
        )
    )

    _require_cloud_llm_consent(
        svc,
        allowed=bool(getattr(args, "allow_cloud_llm", False)),
        tenant=scope.tenant_id,
        workspace=scope.workspace_id,
        project=scope.project_id,
        paths=roots,
    )

    from agentcore_cli.docs_catalog import refresh_docs_catalog_after_sync

    catalog_info: dict[str, Any]
    try:
        catalog_info = refresh_docs_catalog_after_sync(repo_root())
        ui.blank()
        ui.kv(
            "Docs catalog",
            f"built  docs={catalog_info.get('document_count')}  "
            f"tags={catalog_info.get('unique_tags')}  "
            f"cache={catalog_info.get('cache_path')}",
        )
        ui.blank()
    except Exception as exc:  # noqa: BLE001 — sync must not fail on catalog build
        catalog_info = {"ok": False, "error": str(exc)}
        ui.blank()
        ui.kv("Docs catalog", f"build skipped ({exc})")
        ui.blank()

    results: list[dict[str, Any]] = []
    all_tasks: list[dict[str, Any]] = []
    total_in = 0
    total_out = 0
    total_sec = 0.0
    overall = TimedPhase()
    execution_at = execution_at_now()
    for root_path in roots:
        row = _sync_one_root(svc=svc, scope=scope, root_path=root_path, args=args)
        usage = row.pop("_usage", {})
        results.append(row)
        all_tasks.extend(list(usage.get("tasks") or []))
        total_in += int(usage.get("tokens_in") or 0)
        total_out += int(usage.get("tokens_out") or 0)
        total_sec += float(usage.get("duration_sec") or 0.0)
    wall_sec = overall.stop()

    report: dict[str, Any] = {
        "ok": True,
        "paths": [r["path"] for r in results],
        "results": results,
        # Backward-compatible single-root fields when only one path synced
        **(results[0] if len(results) == 1 else {}),
        "docs_catalog": catalog_info,
    }
    usage_record = build_sync_usage_record(
        scope=scope_txt,
        report=report,
        tasks=all_tasks,
        duration_sec=wall_sec if wall_sec > 0 else total_sec,
        tokens_in=total_in,
        tokens_out=total_out,
        execution_at=execution_at,
    )
    log_path = append_sync_usage_record(usage_record)
    ui.blank()
    ui.kv("Execution at", execution_at)
    ui.kv("Usage log", str(log_path))
    ui.blank()
    print_json(report)
    return 0


def cmd_purge(args: argparse.Namespace) -> int:
    if not args.yes:
        raise SystemExit("error: purge requires --yes (destructive: wipes project graph data)")
    svc = _graph_service()
    scope = _graph_scope(args, with_defaults=True)
    ui.blank()
    ui.heading("Purging graph data", success=False)
    ui.kv("Scope", ui.scope_line(scope.tenant_id, scope.workspace_id, scope.project_id))
    result = svc.purge_scope(scope)
    ui.blank()
    ui.heading("Purge complete")
    ui.blank()
    print_json({"ok": True, "purge": result})
    return 0
