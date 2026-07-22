"""`agentcore service` and `agentcore boot` command handlers."""

from __future__ import annotations

import argparse

from agentcore_cli import service_runtime as runtime
from agentcore_cli import ui
from agentcore_cli.sync_progress import format_duration
from agentcore_cli.util import print_json, repo_root


def _print_log_block(title: str, payload: dict) -> None:
    ui.blank()
    ui.section(title)
    path = payload.get("path")
    if path:
        ui.kv("File", str(path))
    if payload.get("exists") is False:
        ui.kv("Content", ui.warn("log file not created yet (process never started)"))
        return
    if payload.get("error"):
        ui.kv("Error", ui.err(str(payload["error"])))
        return
    lines = list(payload.get("lines") or [])
    if not lines:
        ui.kv("Content", ui.dim("(empty)"))
        return
    shown = payload.get("shown")
    total = payload.get("line_count")
    if shown is not None and total is not None:
        ui.kv("Tail", f"last {shown} of {total} lines")
    ui.blank()
    for line in lines:
        print(line)


def _print_service_status(report: dict, *, detail: dict | None = None) -> None:
    state = str(report.get("status") or "")
    okish = state == "all running"
    ui.blank()
    ui.heading("Service", success=okish)
    ui.blank()
    ui.kv("State", ui.status_badge(state))
    ui.kv("Root", str(report.get("repo_root")))
    if report.get("restarted_at"):
        ui.kv("Restarted", str(report["restarted_at"]))
    if report.get("uptime_sec") is not None:
        ui.kv("UpTime", format_duration(float(report["uptime_sec"])))

    compose = report.get("compose") or {}
    ui.blank()
    ui.section("Compose")
    for name, info in (compose.get("services") or {}).items():
        health = str(info.get("health") or "unknown")
        mark = ui.ok(health) if health == "healthy" else ui.err(health)
        ui.kv(str(name), mark)

    mcp = report.get("mcp") or {}
    ui.blank()
    ui.section("MCP HTTP")
    if mcp.get("running"):
        ui.kv("Process", ui.ok(f"pid {mcp.get('pid')}"))
    else:
        ui.kv("Process", ui.err("stopped"))
    ui.kv("Listen", f"{mcp.get('host')}:{mcp.get('port')}")
    reach = ui.ok("yes") if mcp.get("reachable") else ui.err("no")
    ui.kv("Reachable", reach)
    if mcp.get("log"):
        ui.kv("Log", str(mcp["log"]))

    boot = report.get("boot") or {}
    modes = boot.get("modes") or {}
    ui.blank()
    ui.section("Boot")
    for label, info in modes.items():
        enabled = bool(info.get("enabled"))
        present = bool(info.get("unit_file_present"))
        text = "enabled" if enabled else ("unit present" if present else "disabled")
        ui.kv(str(label), ui.ok(text) if enabled else ui.dim(text))

    if detail is not None:
        _print_log_block("Detail — MCP HTTP log", detail.get("mcp_http") or {})
        for name, payload in (detail.get("compose") or {}).items():
            title = f"Detail — Compose {name} log"
            if payload.get("text") is not None and not payload.get("path"):
                ui.blank()
                ui.section(title)
                lines = list(payload.get("lines") or [])
                if payload.get("error"):
                    ui.kv("Error", ui.err(str(payload["error"])))
                elif not lines:
                    ui.kv("Content", ui.dim("(empty)"))
                else:
                    ui.kv("Tail", f"last {len(lines)} lines")
                    ui.blank()
                    for line in lines:
                        print(line)
            else:
                _print_log_block(title, payload)
    elif not okish:
        ui.blank()
        ui.section("Hints")
        ui.bullet("agentcore service detail")
        ui.bullet("agentcore service start")

    ui.blank()


def cmd_service_start(_: argparse.Namespace) -> int:
    root = repo_root()
    ui.blank()
    ui.heading("Starting AgentCore")
    try:
        report = runtime.start_all(root)
    except SystemExit as exc:
        msg = str(exc)
        print(msg, flush=True)
        log_path = runtime.mcp_log_path(root)
        if log_path.is_file():
            tail = runtime.read_log_tail(log_path, lines=80)
            if tail.get("text"):
                ui.blank()
                ui.section("MCP HTTP log (tail)")
                print(tail["text"])
                ui.blank()
        return 1
    ui.blank()
    ui.heading(
        "AgentCore is up" if report.get("ok") else "Start finished with errors",
        success=bool(report.get("ok")),
    )
    print_json(report)
    return 0 if report.get("ok") else 1


def cmd_service_stop(_: argparse.Namespace) -> int:
    root = repo_root()
    ui.blank()
    ui.heading("Stopping AgentCore", success=False)
    report = runtime.stop_all(root)
    ui.blank()
    ui.heading(
        "AgentCore is stopped" if report.get("ok") else "Stop finished with errors",
        success=bool(report.get("ok")),
    )
    print_json(report)
    return 0 if report.get("ok") else 1


def cmd_service_restart(_: argparse.Namespace) -> int:
    root = repo_root()
    ui.blank()
    ui.heading("Restarting AgentCore")
    try:
        report = runtime.restart_all(root)
    except SystemExit as exc:
        print(str(exc), flush=True)
        log_path = runtime.mcp_log_path(root)
        if log_path.is_file():
            tail = runtime.read_log_tail(log_path, lines=80)
            if tail.get("text"):
                ui.blank()
                ui.section("MCP HTTP log (tail)")
                print(tail["text"])
                ui.blank()
        return 1
    ui.blank()
    ui.heading(
        "AgentCore restarted — now up" if report.get("ok") else "Restart finished with errors",
        success=bool(report.get("ok")),
    )
    print_json(report)
    return 0 if report.get("ok") else 1


def cmd_service_status(args: argparse.Namespace) -> int:
    root = repo_root()
    report = runtime.status_all(root)
    if args.json:
        print_json(report)
    else:
        _print_service_status(report)
    return 0 if report.get("status") == "all running" else 1


def cmd_service_detail(args: argparse.Namespace) -> int:
    root = repo_root()
    report = runtime.status_all(root)
    detail = runtime.collect_detail(root, report, lines=80)
    if args.json:
        print_json({**report, "detail": detail})
    else:
        _print_service_status(report, detail=detail)
    return 0 if report.get("status") == "all running" else 1
def cmd_boot_enable(args: argparse.Namespace) -> int:
    root = repo_root()
    report = runtime.boot_enable(root, user=bool(args.user))
    print_json(report)
    return 0 if report.get("ok") else 1


def cmd_boot_disable(args: argparse.Namespace) -> int:
    report = runtime.boot_disable(user=bool(args.user))
    print_json(report)
    return 0 if report.get("ok") else 1
