"""CLI entrypoints: ``agentcore sync`` and ``agentcore purge``."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from agentcore_cli import ui
from agentcore_cli.commands.graph import _graph_scope, _graph_service, _require_cloud_llm_consent
from agentcore_cli.commands.sync.client_remote import cmd_sync_client_remote
from agentcore_cli.commands.sync.one_root import sync_one_root
from agentcore_cli.software_paths import require_software_paths
from agentcore_cli.sync_usage_log import (
    TimedPhase,
    append_sync_usage_record,
    build_sync_usage_record,
    execution_at_now,
)
from agentcore_cli.util import print_json, repo_root


def cmd_sync(args: argparse.Namespace) -> int:
    try:
        return _cmd_sync_body(args)
    except KeyboardInterrupt:
        ui.blank()
        print(f"{ui.warn('!')} Sync stopped — graceful shutdown complete", flush=True)
        ui.blank()
        return 130


def _print_stack_started(started: dict[str, Any]) -> None:
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


def _cmd_sync_body(args: argparse.Namespace) -> int:
    from agentcore_cli.service_runtime import ensure_running_or_offer_start
    from agentcore_cli.service_runtime.paths import local_compose_stack_present
    from code_graph_service.locked_store import apply_sync_compute_limits, resolve_sync_cpu_plan

    cpu_percent = getattr(args, "cpu_percent", None)
    if cpu_percent is not None and str(cpu_percent).strip() != "":
        os.environ["AGENTCORE_SYNC_CPU_PERCENT"] = str(cpu_percent).strip()
    apply_sync_compute_limits(resolve_sync_cpu_plan())

    root = repo_root()
    if not local_compose_stack_present(root):
        return cmd_sync_client_remote(args)

    started = ensure_running_or_offer_start(root)
    if started is not None:
        _print_stack_started(started)

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
        row = sync_one_root(svc=svc, scope=scope, root_path=root_path, args=args)
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
