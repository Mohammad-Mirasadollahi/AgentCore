from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentcore_cli import __version__
from agentcore_cli.state import default_state_root, load_project, save_project
from port_profile import PortProfileError, check_port_available, load_profile, resolve_ports
from port_profile.loader import DEFAULT_PROFILE_PATH
from usage_profile import (
    list_profile_ids,
    load_usage_profile,
    materialize_cursor_mcp_config,
    resolve_effective_profile,
)


def repo_root() -> Path:
    env = os.environ.get("AGENTCORE_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    # backend/packages/agentcore_cli/main.py -> parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def _require_scope(args: argparse.Namespace) -> tuple[str, str, str]:
    tenant = str(args.tenant or "").strip()
    workspace = str(args.workspace or "").strip()
    project = str(args.project or "").strip()
    if not all((tenant, workspace, project)):
        raise SystemExit("error: --tenant, --workspace, and --project are required")
    return tenant, workspace, project


def cmd_version(_: argparse.Namespace) -> int:
    print(f"agentcore {__version__}")
    print(f"root {repo_root()}")
    return 0


def cmd_doctor(_: argparse.Namespace) -> int:
    root = repo_root()
    venv_python = root / ".venv" / "bin" / "python"
    agentcore_bin = root / ".venv" / "bin" / "agentcore"
    ok = True
    checks = {
        "repo_root": str(root),
        "venv_python": venv_python.is_file(),
        "agentcore_on_venv_path": agentcore_bin.is_file(),
        "which_agentcore": shutil.which("agentcore"),
        "profiles": list_profile_ids(),
    }
    for name in ("fastapi", "usage_profile", "agentcore_cli", "mcp_gateway_service"):
        try:
            if name == "mcp_gateway_service":
                sys.path.insert(0, str(root / "backend" / "services" / "mcp-gateway-service" / "src"))
            __import__(name if name != "mcp_gateway_service" else "mcp_gateway_service")
            checks[f"import_{name}"] = True
        except Exception as exc:  # noqa: BLE001
            checks[f"import_{name}"] = f"FAIL: {exc}"
            ok = False
    _print_json(checks)
    return 0 if ok and checks["venv_python"] else 1


def cmd_profile_list(_: argparse.Namespace) -> int:
    for profile_id in list_profile_ids():
        profile = load_usage_profile(profile_id)
        print(f"{profile_id}\t{profile.get('title')}\t{profile.get('audience')}")
    return 0


def cmd_profile_show(args: argparse.Namespace) -> int:
    _print_json(load_usage_profile(args.profile_id))
    return 0


def cmd_project_register(args: argparse.Namespace) -> int:
    tenant, workspace, project_id = _require_scope(args)
    root = default_state_root(repo_root())
    existing = load_project(root, tenant, workspace, project_id)
    if existing and not args.force:
        raise SystemExit(f"error: project already registered at {project_path_msg(root, tenant, workspace, project_id)} (use --force)")
    usage_profile = str(args.usage_profile or "default").strip()
    catalog = load_usage_profile(usage_profile)
    project = {
        "tenant_id": tenant,
        "workspace_id": workspace,
        "project_id": project_id,
        "name": str(args.name or project_id).strip(),
        "usage_profile": usage_profile,
        "domain_pack": str(args.domain_pack or catalog["domain_pack"]),
        "feature_profile": str(args.feature_profile or catalog["feature_profile"]),
        "created_at": _now(),
        "updated_at": _now(),
        "status": "active",
    }
    path = save_project(root, project)
    _print_json({"saved": str(path), "project": project})
    return 0


def project_path_msg(root: Path, tenant: str, workspace: str, project: str) -> str:
    return str(root / tenant / workspace / f"{project}.json")


def cmd_project_activate(args: argparse.Namespace) -> int:
    tenant, workspace, project_id = _require_scope(args)
    root = default_state_root(repo_root())
    project = load_project(root, tenant, workspace, project_id)
    if project is None:
        raise SystemExit("error: project not found; run: agentcore project register ...")
    usage_profile = str(args.usage_profile or "").strip()
    if not usage_profile:
        raise SystemExit("error: --usage-profile is required")
    catalog = load_usage_profile(usage_profile)
    project["usage_profile"] = usage_profile
    if args.apply_catalog_defaults:
        project["domain_pack"] = catalog["domain_pack"]
        project["feature_profile"] = catalog["feature_profile"]
    project["updated_at"] = _now()
    path = save_project(root, project)
    _print_json({"saved": str(path), "project": project})
    return 0


def cmd_project_show(args: argparse.Namespace) -> int:
    tenant, workspace, project_id = _require_scope(args)
    project = load_project(default_state_root(repo_root()), tenant, workspace, project_id)
    if project is None:
        raise SystemExit("error: project not found")
    _print_json(project)
    return 0


def cmd_project_effective(args: argparse.Namespace) -> int:
    tenant, workspace, project_id = _require_scope(args)
    project = load_project(default_state_root(repo_root()), tenant, workspace, project_id)
    if project is None:
        raise SystemExit("error: project not found")
    effective = resolve_effective_profile(
        str(project.get("usage_profile") or "default"),
        tenant_id=tenant,
        workspace_id=workspace,
        project_id=project_id,
        overrides={
            "domain_pack": project.get("domain_pack"),
            "feature_profile": project.get("feature_profile"),
        },
    )
    _print_json(effective)
    return 0


def cmd_cursor_export(args: argparse.Namespace) -> int:
    tenant, workspace, project_id = _require_scope(args)
    root = repo_root()
    project = load_project(default_state_root(root), tenant, workspace, project_id)
    if project is None:
        raise SystemExit("error: project not found")
    effective = resolve_effective_profile(
        str(project.get("usage_profile") or "default"),
        tenant_id=tenant,
        workspace_id=workspace,
        project_id=project_id,
        overrides={
            "domain_pack": project.get("domain_pack"),
            "feature_profile": project.get("feature_profile"),
        },
    )
    python = str(root / ".venv" / "bin" / "python")
    if not Path(python).is_file():
        python = sys.executable
    fragment = materialize_cursor_mcp_config(effective, python_executable=python)
    # Prefer absolute PYTHONPATH for Cursor-launched processes
    abs_paths = [
        root / "backend" / "services" / "mcp-gateway-service" / "src",
        root / "backend" / "packages",
        root / "backend" / "services" / "core-data-service" / "src",
        root / "backend" / "services" / "memory-service" / "src",
        root / "backend" / "services" / "code-graph-service" / "src",
        root / "backend" / "services" / "docs-sync-service" / "src",
    ]
    server_name = next(iter(fragment["mcpServers"]))
    fragment["mcpServers"][server_name]["env"]["PYTHONPATH"] = os.pathsep.join(str(p) for p in abs_paths)
    fragment["mcpServers"][server_name]["cwd"] = str(root)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(fragment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        _print_json(fragment)
    return 0


def cmd_mcp_tools(args: argparse.Namespace) -> int:
    profile_id = str(args.usage_profile or "programming-cursor-mcp").strip()
    profile = load_usage_profile(profile_id)
    for tool in profile["mcp"]["tools"]:
        print(f"{tool['name']}\t{tool['maps_to']}\t{tool['description']}")
    return 0


def cmd_mcp_serve(args: argparse.Namespace) -> int:
    tenant, workspace, project_id = _require_scope(args)
    root = repo_root()
    project = load_project(default_state_root(root), tenant, workspace, project_id)
    usage_profile = str(args.usage_profile or (project or {}).get("usage_profile") or "programming-cursor-mcp")
    env = os.environ.copy()
    env["AGENTCORE_USAGE_PROFILE"] = usage_profile
    env["AGENTCORE_TENANT_ID"] = tenant
    env["AGENTCORE_WORKSPACE_ID"] = workspace
    env["AGENTCORE_PROJECT_ID"] = project_id
    env["AGENTCORE_ROOT"] = str(root)
    pythonpath = os.pathsep.join(
        [
            str(root / "backend" / "services" / "mcp-gateway-service" / "src"),
            str(root / "backend" / "packages"),
            str(root / "backend" / "services" / "core-data-service" / "src"),
            str(root / "backend" / "services" / "memory-service" / "src"),
            str(root / "backend" / "services" / "code-graph-service" / "src"),
            str(root / "backend" / "services" / "docs-sync-service" / "src"),
            env.get("PYTHONPATH", ""),
        ]
    ).strip(os.pathsep)
    env["PYTHONPATH"] = pythonpath
    python = root / ".venv" / "bin" / "python"
    exe = str(python if python.is_file() else sys.executable)
    return subprocess.call([exe, "-m", "mcp_gateway_service"], env=env, cwd=str(root))


def cmd_path_install(args: argparse.Namespace) -> int:
    """Ensure agentcore is available on PATH via ~/.local/bin symlink."""
    root = repo_root()
    source = root / ".venv" / "bin" / "agentcore"
    if not source.is_file():
        raise SystemExit("error: .venv/bin/agentcore missing; run: bash scripts/ensure-venv.sh")
    local_bin = Path(os.path.expanduser("~")) / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)
    target = local_bin / "agentcore"
    if target.is_symlink() or target.exists():
        target.unlink()
    target.symlink_to(source)
    on_path = str(local_bin) in os.environ.get("PATH", "").split(os.pathsep)
    _print_json(
        {
            "symlink": str(target),
            "points_to": str(source),
            "local_bin_on_path": on_path,
            "hint": None
            if on_path
            else f'Add to PATH: export PATH="{local_bin}:$PATH"  (ensure-venv can append this for you)',
        }
    )
    if args.shell_rc and not on_path:
        _ensure_path_export(Path(os.path.expanduser("~")) / args.shell_rc, local_bin)
    return 0


def _ensure_path_export(rc_file: Path, local_bin: Path) -> None:
    line = f'export PATH="{local_bin}:$PATH"  # AgentCore CLI'
    marker = "# AgentCore CLI"
    existing = rc_file.read_text(encoding="utf-8") if rc_file.is_file() else ""
    if marker in existing:
        print(f"PATH export already present in {rc_file}")
        return
    with rc_file.open("a", encoding="utf-8") as handle:
        handle.write(f"\n{line}\n")
    print(f"appended PATH export to {rc_file}")


def _ports_profile_path(args: argparse.Namespace) -> Path | None:
    raw = str(getattr(args, "profile", "") or "").strip()
    return Path(raw) if raw else None


def cmd_ports_show(args: argparse.Namespace) -> int:
    path = _ports_profile_path(args)
    try:
        profile = load_profile(path)
        resolved = resolve_ports(profile)
    except PortProfileError as exc:
        raise SystemExit(f"error: {exc}") from exc
    _print_json({"profile": str(path or DEFAULT_PROFILE_PATH), "ports": resolved})
    return 0


def cmd_ports_check(args: argparse.Namespace) -> int:
    path = _ports_profile_path(args)
    try:
        profile = load_profile(path)
        resolved = resolve_ports(profile)
    except PortProfileError as exc:
        raise SystemExit(f"error: {exc}") from exc
    ports: dict[str, dict[str, Any]] = {}
    ok = True
    for key, port in resolved.items():
        available = check_port_available(port)
        ports[key] = {"port": port, "available": available}
        if not available:
            ok = False
    _print_json({"ok": ok, "ports": ports, "profile": str(path or DEFAULT_PROFILE_PATH)})
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentcore",
        description="AgentCore CLI — manage Usage Profiles, projects, and Cursor MCP",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Show CLI version and repo root")
    sub.add_parser("doctor", help="Check venv, imports, profiles, and PATH")

    profile = sub.add_parser("profile", help="Usage Profile catalog commands")
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)
    profile_sub.add_parser("list", help="List Usage Profiles")
    show = profile_sub.add_parser("show", help="Show one Usage Profile JSON")
    show.add_argument("profile_id")

    project = sub.add_parser("project", help="Local project + Usage Profile state")
    project_sub = project.add_subparsers(dest="project_command", required=True)

    def add_scope(p: argparse.ArgumentParser) -> None:
        p.add_argument("--tenant", required=True)
        p.add_argument("--workspace", required=True)
        p.add_argument("--project", required=True)

    reg = project_sub.add_parser("register", help="Register a local project state file")
    add_scope(reg)
    reg.add_argument("--name", default="")
    reg.add_argument("--usage-profile", default="default")
    reg.add_argument("--domain-pack", default="")
    reg.add_argument("--feature-profile", default="")
    reg.add_argument("--force", action="store_true")

    act = project_sub.add_parser("activate", help="Activate a Usage Profile on a project")
    add_scope(act)
    act.add_argument("--usage-profile", required=True)
    act.add_argument("--apply-catalog-defaults", action=argparse.BooleanOptionalAction, default=True)

    show_p = project_sub.add_parser("show", help="Show local project state")
    add_scope(show_p)
    eff = project_sub.add_parser("effective", help="Resolve effective Usage Profile")
    add_scope(eff)

    cursor = sub.add_parser("cursor", help="Cursor MCP helpers")
    cursor_sub = cursor.add_subparsers(dest="cursor_command", required=True)
    export = cursor_sub.add_parser("export", help="Export mcpServers fragment for Cursor")
    add_scope(export)
    export.add_argument("--out", default="", help="Write JSON to this path")

    mcp = sub.add_parser("mcp", help="MCP gateway helpers")
    mcp_sub = mcp.add_subparsers(dest="mcp_command", required=True)
    tools = mcp_sub.add_parser("tools", help="List MCP tools for a Usage Profile")
    tools.add_argument("--usage-profile", default="programming-cursor-mcp")
    serve = mcp_sub.add_parser("serve", help="Run MCP gateway on stdio for a project scope")
    add_scope(serve)
    serve.add_argument("--usage-profile", default="")

    path_cmd = sub.add_parser("path", help="Install agentcore onto user PATH")
    path_sub = path_cmd.add_subparsers(dest="path_command", required=True)
    install = path_sub.add_parser("install", help="Symlink ~/.local/bin/agentcore -> .venv/bin/agentcore")
    install.add_argument(
        "--shell-rc",
        default="",
        help="Optional rc file to append PATH export (e.g. .bashrc)",
    )

    ports = sub.add_parser("ports", help="Port profile preflight")
    ports_sub = ports.add_subparsers(dest="ports_command", required=True)
    ports_show = ports_sub.add_parser("show", help="Show resolved ports from profile (env overrides)")
    ports_show.add_argument("--profile", default="", help="Port profile JSON path (default: agentcore-dev)")
    ports_check = ports_sub.add_parser("check", help="Check that profile ports are free to bind")
    ports_check.add_argument("--profile", default="", help="Port profile JSON path (default: agentcore-dev)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version and not args.command:
        return cmd_version(args)
    if not args.command:
        parser.print_help()
        return 2

    if args.command == "version":
        return cmd_version(args)
    if args.command == "doctor":
        return cmd_doctor(args)
    if args.command == "profile":
        if args.profile_command == "list":
            return cmd_profile_list(args)
        if args.profile_command == "show":
            return cmd_profile_show(args)
    if args.command == "project":
        if args.project_command == "register":
            return cmd_project_register(args)
        if args.project_command == "activate":
            return cmd_project_activate(args)
        if args.project_command == "show":
            return cmd_project_show(args)
        if args.project_command == "effective":
            return cmd_project_effective(args)
    if args.command == "cursor":
        if args.cursor_command == "export":
            return cmd_cursor_export(args)
    if args.command == "mcp":
        if args.mcp_command == "tools":
            return cmd_mcp_tools(args)
        if args.mcp_command == "serve":
            return cmd_mcp_serve(args)
    if args.command == "path":
        if args.path_command == "install":
            return cmd_path_install(args)
    if args.command == "ports":
        if args.ports_command == "show":
            return cmd_ports_show(args)
        if args.ports_command == "check":
            return cmd_ports_check(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
