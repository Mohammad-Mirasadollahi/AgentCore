"""`agentcore status` — one-shot operator view of local platform state."""

from __future__ import annotations

import argparse
import os
import socket
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from agentcore_cli.cli_defaults import load_dotenv_files, peek_connect_scope, resolve_operator_scope
from agentcore_cli.sync_progress import format_duration, read_live_progress
from agentcore_cli import ui
from agentcore_cli.commands.graph import _graph_service
from agentcore_cli.util import print_json, repo_root


def _tcp_ok(host: str, port: int, *, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _host_port_from_uri(uri: str, default_port: int) -> tuple[str, int] | None:
    raw = (uri or "").strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "tcp://" + raw
    parsed = urlparse(raw)
    host = parsed.hostname or "127.0.0.1"
    port = int(parsed.port or default_port)
    return host, port


def _postgres_probe() -> dict[str, Any]:
    url = os.environ.get("AGENTCORE_DATABASE_URL", "").strip()
    if not url:
        return {"configured": False, "reachable": None}
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = int(parsed.port or 5432)
    return {"configured": True, "host": host, "port": port, "reachable": _tcp_ok(host, port)}


def _neo4j_probe() -> dict[str, Any]:
    uri = os.environ.get("AGENTCORE_NEO4J_URI", "").strip() or "bolt://127.0.0.1:32287"
    parsed = _host_port_from_uri(uri, 7687)
    if parsed is None:
        return {"configured": False, "reachable": None}
    host, port = parsed
    password = os.environ.get("AGENTCORE_NEO4J_PASSWORD", "").strip()
    return {
        "configured": bool(password),
        "uri": uri,
        "host": host,
        "port": port,
        "reachable": _tcp_ok(host, port),
    }


def _mcp_files(work: Path) -> dict[str, bool]:
    paths = {
        "cursor": work / ".cursor" / "mcp.json",
        "vscode": work / ".vscode" / "mcp.json",
        "mcp_json": work / ".mcp.json",
        "agentcore_fragment": work / ".agentcore" / "mcp-servers.json",
    }
    return {name: path.is_file() for name, path in paths.items()}


def _graph_snapshot(tenant: str, workspace: str, project: str) -> dict[str, Any]:
    try:
        svc = _graph_service()
        from code_graph_service.core import Scope

        scope = Scope(tenant, workspace, project)
        symbols = svc.store.list_symbols(scope)
        edges = svc.store.list_edges(scope)
        freshness = svc.freshness_status(scope) if hasattr(svc, "freshness_status") else {}
        pwd = os.environ.get("AGENTCORE_NEO4J_PASSWORD", "").strip()
        backend = os.environ.get("AGENTCORE_GRAPH_CLI_BACKEND", "").strip() or (
            "neo4j"
            if pwd and pwd not in {"replace-with-a-local-secret", "changeme", "password", "neo4j"}
            else "memory"
        )
        return {
            "ok": True,
            "backend": backend,
            "symbol_count": len(symbols),
            "edge_count": len(edges),
            "pending_count": int(freshness.get("pending_count") or 0),
            "pending_files": list(freshness.get("pending_files") or [])[:20],
            "last_sync_at": freshness.get("last_sync_at"),
        }
    except Exception as exc:  # noqa: BLE001 — status must not crash
        return {"ok": False, "error": str(exc)[:500]}


def _overall(report: dict[str, Any]) -> str:
    graph = report.get("graph") or {}
    postgres = report.get("postgres") or {}
    neo4j = report.get("neo4j") or {}
    if not graph.get("ok"):
        return "error"
    pg_down = postgres.get("configured") and postgres.get("reachable") is False
    neo_down = neo4j.get("configured") and neo4j.get("reachable") is False
    if pg_down and neo_down:
        return "Postgres and Neo4j unreachable"
    if pg_down:
        return "Postgres unreachable"
    if neo_down:
        return "Neo4j unreachable"
    if int(graph.get("symbol_count") or 0) == 0:
        return "empty"  # connected but graph not synced yet
    if int(graph.get("pending_count") or 0) > 0:
        return "pending_sync"
    return "ready"


def _rpm_status_snapshot() -> dict[str, Any]:
    """Idle or in-process RPM view (sync process publishes live stats via progress file)."""
    try:
        from code_graph_service.locked_store import sync_max_file_workers

        file_workers = sync_max_file_workers()
    except Exception:  # noqa: BLE001
        file_workers = None
    try:
        svc = _graph_service()
        snap = svc.llm_sessions_snapshot() if hasattr(svc, "llm_sessions_snapshot") else {}
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc)[:300],
            "file_workers_auto": file_workers,
        }
    return {
        "ok": True,
        "configured": bool(snap.get("configured", True)),
        "rpm": int(snap.get("rpm") or 0),
        "inflight_cap": int(snap.get("inflight_cap") or 0),
        "inflight": int(snap.get("inflight_count") or 0),
        "starts_in_window": int(snap.get("starts_in_window") or 0),
        "history_len": len(snap.get("history") or []),
        "file_workers_auto": file_workers,
    }


def build_status_report(
    *,
    tenant: str = "",
    workspace: str = "",
    project: str = "",
    cwd: Path | None = None,
) -> dict[str, Any]:
    load_dotenv_files()
    work = cwd or Path.cwd()
    root = repo_root()
    try:
        from agentcore_cli.remote_client import apply_compose_env_to_os

        apply_compose_env_to_os(os.environ, root)
    except SystemExit:
        pass
    resolved = resolve_operator_scope(tenant=tenant, workspace=workspace, project=project, cwd=work)
    tenant_id, workspace_id, project_id = resolved
    connect = peek_connect_scope()
    from agentcore_cli.identity import identity_path, peek_identity
    from agentcore_cli.software_paths import peek_software_paths

    identity = peek_identity()
    software_paths = peek_software_paths()
    report: dict[str, Any] = {
        "scope": {
            "tenant": tenant_id,
            "workspace": workspace_id,
            "project": project_id,
        },
        "identity_file": str(identity_path()) if identity_path().is_file() else None,
        "identity": identity or None,
        "software_paths": software_paths,
        "repo_root": str(root),
        "cwd": str(work.resolve()),
        "connect_yaml_scope": connect or None,
        "postgres": _postgres_probe(),
        "neo4j": _neo4j_probe(),
        "mcp_configs": _mcp_files(work),
        "graph": _graph_snapshot(tenant_id, workspace_id, project_id),
        "sync_progress": read_live_progress(root=root),
        "rpm": _rpm_status_snapshot(),
    }
    report["status"] = _overall(report)
    hints: list[str] = []
    if report["status"] == "empty":
        hints.append("run: agentcore sync")
    if report["status"] == "pending_sync":
        hints.append("run: agentcore sync")
    status = str(report["status"])
    if "Postgres" in status:
        hints.append("start Compose postgres (install.sh / agentcore service start)")
    if "Neo4j" in status:
        hints.append("start Compose neo4j, then: agentcore sync")
    if status == "error":
        hints.append("check agentcore doctor and Neo4j/Postgres")
    if not any(report["mcp_configs"].values()):
        hints.append("run: agentcore connect --local")
    if not report.get("identity_file"):
        hints.append("run: agentcore init --tenant <id> --workspace <id> --path <app-root>")
    elif not software_paths:
        hints.append("run: agentcore paths add /path/to/app")
    report["hints"] = hints
    return report


def _print_human(report: dict[str, Any]) -> None:
    scope = report["scope"]
    status = str(report["status"])
    okish = status not in {"error"} and "unreachable" not in status
    ui.blank()
    ui.heading("Status", success=okish)
    ui.blank()
    ui.kv("State", ui.status_badge(str(report["status"])))
    ui.kv("Scope", ui.scope_line(scope["tenant"], scope["workspace"], scope["project"]))
    if report.get("identity_file"):
        ui.kv("Identity", str(report["identity_file"]))
    soft = report.get("software_paths") or []
    if soft:
        ui.kv("Paths", f"{len(soft)} root(s)")
        for p in soft:
            ui.bullet(str(p))
    else:
        ui.kv("Paths", ui.warn("none — agentcore paths add /path/to/app"))

    live = report.get("sync_progress")
    if isinstance(live, dict) and live:
        ui.blank()
        ui.section("Live sync")
        pct = float(live.get("percent") or 0)
        eta = live.get("eta_sec")
        ui.kv(
            "Progress",
            f"{pct:.1f}%  ({live.get('done')}/{live.get('total')} "
            f"{live.get('phase') or 'files'})",
        )
        in_flight = int(live.get("files_in_flight") or 0)
        workers = int(live.get("file_workers") or 0)
        if workers or in_flight:
            ui.kv(
                "Parallel files",
                f"{in_flight} active / {workers or '?'} workers",
            )
            paths = list(live.get("files_in_flight_paths") or [])
            if paths:
                ui.kv("Active", ", ".join(str(p) for p in paths[:6]))
        rpm_cap = int(live.get("rpm_inflight_cap") or live.get("rpm") or 0)
        if rpm_cap or live.get("rpm"):
            ui.kv(
                "RPM",
                f"inflight {int(live.get('rpm_inflight') or 0)}/{rpm_cap or int(live.get('rpm') or 0)}  "
                f"starts {int(live.get('rpm_starts_in_window') or 0)}/{int(live.get('rpm') or 0)} "
                f"(rolling 60s)",
            )
        ui.kv("Elapsed", format_duration(float(live.get("elapsed_sec") or 0)))
        ui.kv(
            "ETA",
            "…" if eta is None else format_duration(float(eta)),
        )
        rate = live.get("files_per_sec")
        if rate:
            ui.kv("Rate", f"{float(rate):.2f} files/s")
        ui.kv("Symbols", str(live.get("symbols_indexed") or 0))
        ui.kv("≈Tokens", str(live.get("approx_tokens") or 0))
        if live.get("file"):
            ui.kv("File", str(live["file"]))

    rpm = report.get("rpm") or {}
    live = report.get("sync_progress") if isinstance(report.get("sync_progress"), dict) else None
    ui.blank()
    ui.section("LLM RPM")
    # Prefer stats published by an active sync process (separate PID).
    if live and int(live.get("rpm") or 0) > 0:
        cap = int(live.get("rpm_inflight_cap") or live.get("rpm") or 0)
        limit = int(live.get("rpm") or 0)
        ui.kv("Limit", f"{limit} req/min  (inflight cap {cap})")
        ui.kv(
            "Now",
            f"inflight {int(live.get('rpm_inflight') or 0)}/{cap}  "
            f"starts {int(live.get('rpm_starts_in_window') or 0)}/{limit}  "
            f"(from live sync pid {live.get('pid')})",
        )
        workers = int(live.get("file_workers") or 0)
        in_flight = int(live.get("files_in_flight") or 0)
        if workers or in_flight:
            ui.kv("Parallel files", f"{in_flight} active / {workers or '?'} workers")
    elif rpm.get("ok"):
        cap = int(rpm.get("inflight_cap") or rpm.get("rpm") or 0)
        ui.kv(
            "Limit",
            f"{int(rpm.get('rpm') or 0)} req/min  (inflight cap {cap})",
        )
        ui.kv(
            "Now",
            f"inflight {int(rpm.get('inflight') or 0)}/{cap}  "
            f"starts {int(rpm.get('starts_in_window') or 0)}/{int(rpm.get('rpm') or 0)}",
        )
        if rpm.get("file_workers_auto") is not None:
            ui.kv("File workers", f"auto → {rpm.get('file_workers_auto')}")
    else:
        ui.kv("RPM", ui.warn(str(rpm.get("error") or "unavailable")))

    pg = report["postgres"]
    if pg.get("configured"):
        pg_txt = ui.ok("up") if pg.get("reachable") else ui.err("DOWN")
        ui.kv("Postgres", f"{pg_txt}  {pg.get('host')}:{pg.get('port')}")
    else:
        ui.kv("Postgres", ui.dim("not configured"))

    neo = report["neo4j"]
    if neo.get("configured"):
        neo_txt = ui.ok("up") if neo.get("reachable") else ui.err("DOWN")
        ui.kv("Neo4j", f"{neo_txt}  {neo.get('uri')}")
    else:
        ui.kv("Neo4j", ui.dim("not configured (graph may be in-memory)"))

    graph = report["graph"]
    if graph.get("ok"):
        ui.kv(
            "Graph",
            f"backend={graph.get('backend')}  "
            f"symbols={graph.get('symbol_count')}  edges={graph.get('edge_count')}  "
            f"pending={graph.get('pending_count')}",
        )
    else:
        ui.kv("Graph", ui.err(f"ERROR {graph.get('error')}"))

    mcp = report["mcp_configs"]
    present = [k for k, v in mcp.items() if v]
    ui.kv("MCP", ", ".join(present) if present else ui.warn("none — run connect --local"))

    hints = report.get("hints") or []
    if hints:
        ui.blank()
        ui.section("Hints")
        for hint in hints:
            ui.bullet(hint)
    ui.blank()


def cmd_status(args: argparse.Namespace) -> int:
    report = build_status_report(
        tenant=str(args.tenant or ""),
        workspace=str(args.workspace or ""),
        project=str(args.project or ""),
        cwd=Path.cwd(),
    )
    if args.json:
        print_json(report)
    else:
        _print_human(report)
        if args.verbose:
            print("---")
            print_json(report)
    status = str(report["status"])
    code = 0
    if status == "error" or "unreachable" in status:
        code = 1
    return code
