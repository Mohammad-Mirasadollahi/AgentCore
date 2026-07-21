"""Remote dev host → AgentCore server MCP wiring (SSH stdio)."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

from agentcore_cli.mcp_client_targets import (
    DEFAULT_SERVER_NAME,
    merge_mcp_servers_file,
    resolve_client_ids,
    write_fragment_to_clients,
)

REMOTE_MCP_SERVE_MODULE = "agentcore_cli.remote_mcp_serve"


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a KEY=VALUE env file (no shell expansion)."""
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip()
    return out


def apply_compose_env_to_os(environ: dict[str, str], repo_root: Path) -> None:
    """Load ``backend/deployments/compose/.env.local`` into *environ* and set MCP store URLs."""
    env_file = repo_root / "backend" / "deployments" / "compose" / ".env.local"
    values = parse_env_file(env_file)
    if not values:
        raise SystemExit(f"error: missing or empty compose env {env_file} (run install.sh on AgentCore host)")

    required = (
        "AGENTCORE_POSTGRES_USER",
        "AGENTCORE_POSTGRES_PASSWORD",
        "AGENTCORE_POSTGRES_PORT",
        "AGENTCORE_POSTGRES_DATABASE",
        "AGENTCORE_NEO4J_BOLT_PORT",
        "AGENTCORE_NEO4J_PASSWORD",
    )
    missing = [k for k in required if not values.get(k)]
    if missing:
        raise SystemExit(f"error: compose env missing keys: {', '.join(missing)}")

    environ.update(values)
    pg_user = values["AGENTCORE_POSTGRES_USER"]
    pg_pass = values["AGENTCORE_POSTGRES_PASSWORD"]
    pg_port = values["AGENTCORE_POSTGRES_PORT"]
    pg_db = values["AGENTCORE_POSTGRES_DATABASE"]
    bolt_port = values["AGENTCORE_NEO4J_BOLT_PORT"]
    neo_user = values.get("AGENTCORE_NEO4J_USER", "neo4j")

    environ["AGENTCORE_DATABASE_URL"] = (
        f"postgresql://{pg_user}:{pg_pass}@127.0.0.1:{pg_port}/{pg_db}"
    )
    environ["AGENTCORE_MCP_STORE_MODE"] = "postgres"
    environ["AGENTCORE_NEO4J_URI"] = f"bolt://127.0.0.1:{bolt_port}"
    environ["AGENTCORE_NEO4J_USER"] = neo_user
    environ["AGENTCORE_CODE_GRAPH_STORE"] = "neo4j"
    environ["AGENTCORE_MCP_GRAPH_MODE"] = "neo4j"


def remote_venv_python(remote_root: str, *, remote_os: str = "unix") -> str:
    """Return the remote venv Python path (Linux/macOS default; Windows optional)."""
    root = remote_root.rstrip("/\\")
    if remote_os == "windows":
        return f"{root}/.venv/Scripts/python.exe"
    return f"{root}/.venv/bin/python"


def remote_mcp_serve_command(
    remote_root: str,
    tenant: str,
    workspace: str,
    project_id: str,
    *,
    remote_python: str | None = None,
    remote_os: str = "unix",
) -> list[str]:
    """Argv fragment executed on the AgentCore host (after SSH)."""
    py = remote_python or remote_venv_python(remote_root, remote_os=remote_os)
    return [py, "-m", REMOTE_MCP_SERVE_MODULE, tenant, workspace, project_id]


def ssh_argv(
    ssh_target: str,
    remote_command: Sequence[str],
    *,
    batch_mode: bool = True,
    connect_timeout: int = 15,
) -> list[str]:
    """Full local argv to run *remote_command* on *ssh_target*."""
    cmd: list[str] = ["ssh"]
    if batch_mode:
        cmd.extend(["-o", "BatchMode=yes"])
    if connect_timeout > 0:
        cmd.extend(["-o", f"ConnectTimeout={connect_timeout}"])
    cmd.append(ssh_target)
    cmd.extend(remote_command)
    return cmd


def materialize_ssh_mcp_fragment(
    *,
    ssh_target: str,
    remote_root: str,
    tenant: str,
    workspace: str,
    project_id: str,
    server_name: str = DEFAULT_SERVER_NAME,
    remote_python: str | None = None,
    remote_os: str = "unix",
    ssh_batch_mode: bool = True,
    ssh_connect_timeout: int = 15,
) -> dict[str, Any]:
    """Build an ``mcpServers`` fragment that runs MCP gateway on the AgentCore host via SSH."""
    remote_cmd = remote_mcp_serve_command(
        remote_root,
        tenant,
        workspace,
        project_id,
        remote_python=remote_python,
        remote_os=remote_os,
    )
    args: list[str] = []
    if ssh_batch_mode:
        args.extend(["-o", "BatchMode=yes"])
    if ssh_connect_timeout > 0:
        args.extend(["-o", f"ConnectTimeout={ssh_connect_timeout}"])
    args.append(ssh_target)
    args.extend(remote_cmd)
    return {
        "mcpServers": {
            server_name: {
                "command": "ssh",
                "args": args,
            }
        }
    }


def run_ssh(ssh_target: str, remote_command: Sequence[str], *, connect_timeout: int = 15) -> int:
    return subprocess.run(ssh_argv(ssh_target, remote_command, connect_timeout=connect_timeout)).returncode


def doctor_remote(
    ssh_target: str,
    remote_root: str,
    *,
    remote_python: str | None = None,
    remote_os: str = "unix",
    connect_timeout: int = 15,
) -> int:
    """Verify SSH and remote AgentCore MCP prerequisites."""
    root = remote_root.rstrip("/\\")
    py = remote_python or remote_venv_python(root, remote_os=remote_os)
    agentcore = f"{root}/.venv/bin/agentcore" if remote_os != "windows" else f"{root}/.venv/Scripts/agentcore.exe"
    checks: list[tuple[str, list[str]]] = [
        ("remote python", ["test", "-f", py]),
        ("remote agentcore", ["test", "-f", agentcore]),
        (
            "remote mcp serve module",
            [py, "-c", f"import {REMOTE_MCP_SERVE_MODULE.split('.')[0]}; import {REMOTE_MCP_SERVE_MODULE}"],
        ),
    ]
    ok = True
    for label, remote_cmd in checks:
        code = run_ssh(ssh_target, remote_cmd, connect_timeout=connect_timeout)
        if code != 0:
            ok = False
            print(f"FAIL {label}: ssh {ssh_target} {' '.join(shlex.quote(c) for c in remote_cmd)}", file=sys.stderr)
        else:
            print(f"OK {label}")
    return 0 if ok else 1


def remote_register_project(
    ssh_target: str,
    remote_root: str,
    tenant: str,
    workspace: str,
    project_id: str,
    *,
    project_name: str,
    usage_profile: str,
    remote_os: str = "unix",
) -> None:
    root = remote_root.rstrip("/\\")
    if remote_os == "windows":
        agentcore = f"{root}/.venv/Scripts/agentcore.exe"
        shell = (
            f"cd /d {root} && "
            f"{agentcore} project register "
            f"--tenant {tenant} --workspace {workspace} --project {project_id} "
            f"--name {json.dumps(project_name)} --usage-profile {usage_profile} --force && "
            f"{agentcore} project activate "
            f"--tenant {tenant} --workspace {workspace} --project {project_id} "
            f"--usage-profile {usage_profile}"
        )
        remote_cmd = ["cmd", "/c", shell]
    else:
        agentcore = f"{root}/.venv/bin/agentcore"
        shell = (
            f"set -euo pipefail; cd {shlex.quote(root)}; "
            f"{shlex.quote(agentcore)} project register "
            f"--tenant {shlex.quote(tenant)} --workspace {shlex.quote(workspace)} "
            f"--project {shlex.quote(project_id)} "
            f"--name {json.dumps(project_name)} --usage-profile {shlex.quote(usage_profile)} --force; "
            f"{shlex.quote(agentcore)} project activate "
            f"--tenant {shlex.quote(tenant)} --workspace {shlex.quote(workspace)} "
            f"--project {shlex.quote(project_id)} "
            f"--usage-profile {shlex.quote(usage_profile)}"
        )
        remote_cmd = ["bash", "-lc", shell]
    code = run_ssh(ssh_target, remote_cmd)
    if code != 0:
        raise SystemExit(f"error: remote project register/activate failed (exit {code})")


def wire_remote_dev_host(
    *,
    ssh_target: str,
    remote_root: str,
    tenant: str,
    workspace: str,
    project_id: str,
    out_path: Path | None,
    server_name: str = DEFAULT_SERVER_NAME,
    project_dir: Path | None = None,
    register: bool = False,
    project_name: str = "",
    usage_profile: str = "programming-cursor-mcp",
    dry_run: bool = False,
    remote_python: str | None = None,
    remote_os: str = "unix",
    skip_doctor: bool = False,
    clients: str = "all",
    include_user_clients: bool = False,
) -> int:
    if not skip_doctor:
        py = remote_python or remote_venv_python(remote_root, remote_os=remote_os)
        if run_ssh(ssh_target, ["test", "-f", py]) != 0:
            raise SystemExit(f"error: remote python missing at {py} (run install.sh on AgentCore host)")

    if register:
        remote_register_project(
            ssh_target,
            remote_root,
            tenant,
            workspace,
            project_id,
            project_name=project_name or project_id,
            usage_profile=usage_profile,
            remote_os=remote_os,
        )

    fragment = materialize_ssh_mcp_fragment(
        ssh_target=ssh_target,
        remote_root=remote_root,
        tenant=tenant,
        workspace=workspace,
        project_id=project_id,
        server_name=server_name,
        remote_python=remote_python,
        remote_os=remote_os,
    )

    if dry_run:
        print(json.dumps(fragment, indent=2, sort_keys=True))
        return 0

    base = project_dir or Path.cwd()
    if out_path:
        merge_mcp_servers_file(out_path, fragment, server_names=(server_name,))
        print(f"wrote {out_path}")
    else:
        client_ids = resolve_client_ids(clients)
        written = write_fragment_to_clients(
            base,
            fragment,
            client_ids,
            server_name=server_name,
            include_user_clients=include_user_clients,
        )
        for path in written:
            print(f"wrote {path}")
    print("Reload MCP in your coding agent / IDE.")
    return 0
