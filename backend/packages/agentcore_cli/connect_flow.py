"""Orchestration for `agentcore connect` (HTTP preferred, SSH fallback)."""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import httpx

from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.connect_security import validate_connect_settings
from agentcore_cli.mcp_client_targets import (
    DEFAULT_SERVER_NAME,
    materialize_http_mcp_fragment,
    resolve_client_ids,
    write_fragment_to_clients,
)
from agentcore_cli.remote_client import (
    doctor_remote,
    materialize_ssh_mcp_fragment,
    remote_register_project,
)


def _ssh_command(settings: ConnectSettings, remote_command: list[str], *, connect_timeout: int = 15) -> list[str]:
    from agentcore_cli.remote_client import ssh_argv

    extra: list[str] = []
    if settings.ssh_identity.strip():
        extra.extend(["-i", str(Path(settings.ssh_identity).expanduser())])
    base = ssh_argv(settings.ssh, remote_command, connect_timeout=connect_timeout)
    return ["ssh", *extra, *base[1:]]


def _run_ssh(settings: ConnectSettings, remote_command: list[str], *, connect_timeout: int = 15) -> int:
    return subprocess.run(_ssh_command(settings, remote_command, connect_timeout=connect_timeout)).returncode


def _api_headers(settings: ConnectSettings) -> dict[str, str]:
    headers = {
        "X-Tenant-Id": settings.tenant,
        "X-Workspace-Id": settings.workspace,
        "X-Actor-Id": settings.actor_id,
        "Idempotency-Key": str(uuid.uuid4()),
    }
    if settings.api_token:
        headers["Authorization"] = f"Bearer {settings.api_token}"
    return headers


def api_bootstrap(settings: ConnectSettings) -> dict[str, Any]:
    if not settings.api_url:
        return {}
    body: dict[str, Any] = {
        "name": settings.project_name,
        "usage_profile": settings.usage_profile,
    }
    if settings.source_server_path:
        body["source_path"] = settings.source_server_path
    if settings.source_git_remote:
        body["git"] = {"remote": settings.source_git_remote, "branch": settings.source_git_branch}
    if settings.mcp_http_url:
        body["mcp_http_url"] = settings.mcp_http_url
    url = f"{settings.api_url}/api/v1/projects/{settings.project}/connect/bootstrap"
    try:
        response = httpx.post(url, headers=_api_headers(settings), json=body, timeout=30.0)
    except httpx.HTTPError as exc:
        raise SystemExit(f"error: connect bootstrap request failed: {exc}") from exc
    if response.status_code >= 400:
        raise SystemExit(f"error: bootstrap HTTP {response.status_code}: {response.text[:500]}")
    return response.json()


def api_ingest(settings: ConnectSettings) -> dict[str, Any]:
    if not settings.api_url:
        return {}
    body: dict[str, Any] = {}
    if settings.source_server_path:
        body["source_path"] = settings.source_server_path
    url = f"{settings.api_url}/api/v1/projects/{settings.project}/connect/ingest"
    try:
        response = httpx.post(url, headers=_api_headers(settings), json=body, timeout=120.0)
    except httpx.HTTPError as exc:
        raise SystemExit(f"error: connect ingest request failed: {exc}") from exc
    if response.status_code >= 400:
        raise SystemExit(f"error: ingest HTTP {response.status_code}: {response.text[:500]}")
    return response.json()


def api_health(settings: ConnectSettings) -> bool:
    if not settings.api_url:
        return False
    try:
        response = httpx.get(f"{settings.api_url}/health", timeout=10.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def mcp_http_smoke(url: str, headers: dict[str, str]) -> bool:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=15.0)
    except httpx.HTTPError:
        return False
    if response.status_code >= 400:
        return False
    data = response.json()
    return isinstance(data, dict) and "result" in data


def reachability_check(settings: ConnectSettings) -> None:
    if settings.api_url and not api_health(settings):
        raise SystemExit(f"error: API health check failed for {settings.api_url}/health")
    if settings.ssh and _run_ssh(settings, ["true"]) != 0:
        raise SystemExit(f"error: SSH reachability failed for {settings.ssh} (use key-based auth)")


def remote_ingest(settings: ConnectSettings) -> int:
    if not settings.source_server_path or not settings.ssh:
        return 0
    root = settings.remote_root.rstrip("/\\")
    agentcore = f"{root}/.venv/bin/agentcore"
    remote_cmd = [
        agentcore,
        "graph",
        "ingest",
        "--tenant",
        settings.tenant,
        "--workspace",
        settings.workspace,
        "--project",
        settings.project,
        "--path",
        settings.source_server_path,
    ]
    print(f"ingest: {settings.source_server_path} on server …")
    return _run_ssh(settings, remote_cmd)


def _should_ingest(settings: ConnectSettings) -> bool:
    if not settings.source_server_path and not settings.source_git_remote:
        return False
    mode = settings.ingest_mode
    if mode == "off":
        return False
    if mode == "always":
        return True
    return mode in ("optional", "if_source", "true", "yes")


def _write_clients(work: Path, fragment: dict[str, Any], settings: ConnectSettings) -> list[Path]:
    client_ids = resolve_client_ids(settings.clients)
    written = write_fragment_to_clients(
        work,
        fragment,
        client_ids,
        server_name=DEFAULT_SERVER_NAME,
        include_user_clients=settings.include_user_clients,
    )
    for path in written:
        print(f"wrote {path}")
    print("Reload MCP in your coding agent / IDE.")
    return written


def run_connect(
    settings: ConnectSettings,
    *,
    project_dir: Path | None = None,
    dry_run: bool = False,
) -> int:
    work = project_dir or Path.cwd()
    for line in validate_connect_settings(settings):
        print(line, file=sys.stderr)
    reachability_check(settings)
    print(
        f"connect: scope={settings.tenant}/{settings.workspace}/{settings.project} "
        f"(concurrent agents share this project store; each IDE session is an independent MCP client)"
    )

    bootstrap: dict[str, Any] = {}
    registered_via_api = False
    if settings.api_url and settings.register:
        bootstrap = api_bootstrap(settings)
        registered_via_api = True
        if bootstrap:
            print("bootstrap OK:", json.dumps(bootstrap.get("scope", {}), sort_keys=True))

    mcp_info = bootstrap.get("mcp") if isinstance(bootstrap.get("mcp"), dict) else {}
    http_url = str(mcp_info.get("url") or settings.mcp_http_url or "").strip()
    if http_url and not http_url.endswith("/mcp"):
        http_url = http_url.rstrip("/") + "/mcp"
    http_headers = dict(mcp_info.get("headers") or {})
    if settings.prefer_http and http_url and http_headers:
        fragment = materialize_http_mcp_fragment(url=http_url, headers=http_headers)
        if dry_run:
            print(json.dumps(fragment, indent=2, sort_keys=True))
            return 0
        _write_clients(work, fragment, settings)
        if settings.smoke_test and not mcp_http_smoke(http_url, http_headers):
            print("warn: MCP HTTP smoke (initialize) failed; check serve-http and token", file=sys.stderr)
        else:
            print(f"transport: streamable_http ({http_url})")
        if _should_ingest(settings):
            if settings.api_url:
                result = api_ingest(settings)
                print("ingest:", json.dumps(result.get("ingest", result), sort_keys=True))
            elif settings.ssh:
                code = remote_ingest(settings)
                if code != 0:
                    print("warn: graph ingest exited non-zero", code)
        return 0

    if not settings.ssh:
        raise SystemExit(
            "error: HTTP MCP unavailable (set server.mcp_http_url + token secret on server, "
            "or set server.ssh for Phase A stdio fallback)"
        )

    if settings.register and not dry_run and not registered_via_api:
        remote_register_project(
            settings.ssh,
            settings.remote_root,
            settings.tenant,
            settings.workspace,
            settings.project,
            project_name=settings.project_name,
            usage_profile=settings.usage_profile,
            remote_os=settings.remote_os,
        )

    if settings.smoke_test and not dry_run:
        if doctor_remote(settings.ssh, settings.remote_root, remote_os=settings.remote_os) != 0:
            raise SystemExit("error: remote doctor failed")

    fragment = materialize_ssh_mcp_fragment(
        ssh_target=settings.ssh,
        remote_root=settings.remote_root,
        tenant=settings.tenant,
        workspace=settings.workspace,
        project_id=settings.project,
        remote_os=settings.remote_os,
    )
    if dry_run:
        print(json.dumps(fragment, indent=2, sort_keys=True))
        return 0
    _write_clients(work, fragment, settings)
    print("transport: ssh-stdio")

    if _should_ingest(settings) and not dry_run:
        if settings.api_url:
            result = api_ingest(settings)
            print("ingest:", json.dumps(result.get("ingest", result), sort_keys=True))
        else:
            ingest_code = remote_ingest(settings)
            if ingest_code != 0:
                print("warn: graph ingest exited non-zero", ingest_code)
    return 0
