"""Orchestration for `agentcore connect` (HTTP preferred, SSH fallback)."""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import httpx

from agentcore_cli import state
from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.connect_security import validate_connect_settings
from agentcore_cli.local_mcp import materialize_local_stdio_fragment
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
from agentcore_cli.util import now_iso, repo_root
from agentcore_cli import ui
from usage_profile import load_usage_profile


def _materialize_mcp_first_guidance(work: Path) -> dict[str, Any]:
    """Write always-apply MCP-first rule/skills so agents prefer AgentCore without waiting on resolve."""
    try:
        from common_context_service.guidance_export import materialize_mcp_first_seed
    except ImportError:
        return {"written": [], "skipped": [], "conflicts": [], "error": "common_context_service unavailable"}
    return materialize_mcp_first_seed(work, layout="cursor", force=False)


def _ssh_command(settings: ConnectSettings, remote_command: list[str], *, connect_timeout: int = 15) -> list[str]:
    from agentcore_cli.remote_client import ssh_argv

    return ssh_argv(
        settings.ssh,
        remote_command,
        connect_timeout=connect_timeout,
        identity_file=settings.ssh_identity or None,
    )


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
    if settings.local:
        return
    if settings.api_url and not api_health(settings):
        raise SystemExit(f"error: API health check failed for {settings.api_url}/health")
    # Prefer HTTP when URL + token can wire MCP; do not require SSH BatchMode in that case.
    http_ready = bool(settings.prefer_http and settings.mcp_http_url and settings.api_token)
    if settings.ssh and not http_ready and _run_ssh(settings, ["true"]) != 0:
        raise SystemExit(
            f"error: SSH reachability failed for {settings.ssh} (BatchMode / key auth). "
            "Run `agentcore connect edit` to re-auth and replace the AgentCore pubkey, "
            "or fix auth.ssh_key in .agentcore/connect.yaml."
        )


def _local_register(settings: ConnectSettings) -> Path:
    root = state.default_state_root(repo_root())
    catalog = load_usage_profile(settings.usage_profile)
    existing = state.load_project(root, settings.tenant, settings.workspace, settings.project)
    project = existing or {
        "tenant_id": settings.tenant,
        "workspace_id": settings.workspace,
        "project_id": settings.project,
        "created_at": now_iso(),
        "status": "active",
    }
    project.update(
        {
            "name": settings.project_name or settings.project,
            "usage_profile": settings.usage_profile,
            "domain_pack": catalog["domain_pack"],
            "feature_profile": catalog["feature_profile"],
            "updated_at": now_iso(),
        }
    )
    path = state.save_project(root, project)
    return path


def remote_ingest(settings: ConnectSettings) -> int:
    if not settings.source_server_path or not settings.ssh:
        return 0
    root = settings.remote_root.rstrip("/\\")
    agentcore = f"{root}/.venv/bin/agentcore"
    remote_cmd = [
        agentcore,
        "sync",
        "--tenant",
        settings.tenant,
        "--workspace",
        settings.workspace,
        "--project",
        settings.project,
        "--path",
        settings.source_server_path,
    ]
    print(f"   {ui.warn('…')} syncing {settings.source_server_path} on server")
    return _run_ssh(settings, remote_cmd)


def remote_sync_from_args(settings: ConnectSettings, args: Any) -> int:
    """Run `agentcore sync` on the connected server (client checkout path)."""
    if not settings.ssh:
        raise SystemExit("error: connect.yaml has no server.ssh for remote sync")
    root = settings.remote_root.rstrip("/\\")
    agentcore = f"{root}/.venv/bin/agentcore"
    tenant = str(getattr(args, "tenant", None) or settings.tenant or "default")
    workspace = str(getattr(args, "workspace", None) or settings.workspace or "default")
    project = str(getattr(args, "project", None) or settings.project or "project")
    remote_cmd = [
        agentcore,
        "sync",
        "--tenant",
        tenant,
        "--workspace",
        workspace,
        "--project",
        project,
    ]
    paths = list(getattr(args, "path", None) or [])
    if paths:
        for path in paths:
            remote_cmd.extend(["--path", str(path)])
        target = ", ".join(str(p) for p in paths)
    elif settings.source_server_path:
        remote_cmd.extend(["--path", settings.source_server_path])
        target = settings.source_server_path
    else:
        target = "server pinned software paths"
    max_files = getattr(args, "max_files", None)
    if max_files is not None:
        remote_cmd.extend(["--max-files", str(max_files)])
    if getattr(args, "force", False):
        remote_cmd.append("--force")
    if getattr(args, "allow_cloud_llm", False):
        remote_cmd.append("--allow-cloud-llm")
    print(f"   {ui.warn('…')} remote sync on server ({target})")
    return _run_ssh(settings, remote_cmd)


def _local_ingest(settings: ConnectSettings, path: str) -> int:
    root = repo_root()
    agentcore = root / ".venv" / "bin" / "agentcore"
    exe = str(agentcore if agentcore.is_file() else "agentcore")
    print(f"   {ui.warn('…')} syncing {path} (local)")
    return subprocess.run(
        [
            exe,
            "sync",
            "--tenant",
            settings.tenant,
            "--workspace",
            settings.workspace,
            "--project",
            settings.project,
            "--path",
            path,
        ],
        cwd=str(root),
    ).returncode


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
    return write_fragment_to_clients(
        work,
        fragment,
        client_ids,
        server_name=DEFAULT_SERVER_NAME,
        include_user_clients=settings.include_user_clients,
    )


def _guidance_connect_notes(guidance: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    if guidance.get("error"):
        notes.append(f"MCP-first guidance skip: {guidance['error']}")
        return notes
    written = guidance.get("written") or []
    conflicts = guidance.get("conflicts") or []
    removed = guidance.get("removed") or []
    version = guidance.get("seed_pack_version")
    if written:
        ver = f" @ {version}" if version else ""
        notes.append(f"Materialized MCP-first guidance ({len(written)} file(s){ver})")
    elif version and not conflicts and not removed:
        notes.append(f"MCP-first guidance up to date ({version})")
    if removed:
        notes.append(f"Removed retired MCP-first guidance file(s): {len(removed)}")
    if conflicts:
        paths = ", ".join(str(c.get("path")) for c in conflicts[:3])
        more = "" if len(conflicts) <= 3 else f" (+{len(conflicts) - 3} more)"
        notes.append(f"Skipped conflicting guidance path(s): {paths}{more}")
    return notes


def _print_connect_summary(
    *,
    settings: ConnectSettings,
    transport: str,
    project_state: Path | None,
    written: list[Path],
    work: Path,
    extra_notes: list[str] | None = None,
) -> None:
    ui.blank()
    ui.heading("Connect complete")
    ui.blank()
    ui.kv("Scope", ui.scope_line(settings.tenant, settings.workspace, settings.project))
    ui.kv("Profile", settings.usage_profile)
    ui.kv("Transport", transport)
    if project_state is not None:
        ui.kv("Project", str(project_state))
    ui.blank()
    ui.section("What happened")
    ui.bullet("Registered / refreshed local project state for this scope")
    ui.bullet("Wrote MCP server configs so your IDE can talk to AgentCore")
    for note in extra_notes or []:
        ui.bullet(note)
    if written:
        ui.blank()
        ui.section("MCP configs written")
        for rel in ui.summarize_paths(written, relative_to=str(work)):
            ui.bullet(rel)
    steps = [
        "Reload MCP / the IDE window",
        "Check health: agentcore status",
        "Fill the graph: agentcore sync",
    ]
    if transport.startswith("ssh") or transport == "ssh-stdio":
        steps.append(
            "Hand-edit .agentcore/connect.yaml for scope/clients; "
            "run agentcore connect edit to change SSH host/user (replaces pubkey)"
        )
    ui.next_steps(steps)

    ui.blank()


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
    ui.blank()
    print(f"{ui.accent('→')}  Connecting {ui.scope_line(settings.tenant, settings.workspace, settings.project)}")
    print(
        f"   {ui.dim('Agents sharing this scope use the same store; each IDE session is its own MCP client.')}"
    )

    bootstrap: dict[str, Any] = {}
    registered_via_api = False
    if settings.api_url and settings.register:
        bootstrap = api_bootstrap(settings)
        registered_via_api = True
        if bootstrap:
            print(f"   {ui.ok('✔')} API bootstrap OK")

    mcp_info = bootstrap.get("mcp") if isinstance(bootstrap.get("mcp"), dict) else {}
    http_url = str(mcp_info.get("url") or settings.mcp_http_url or "").strip()
    if http_url and not http_url.endswith("/mcp"):
        http_url = http_url.rstrip("/") + "/mcp"
    http_headers = dict(mcp_info.get("headers") or {})
    # Shared AGENTCORE_MCP_HTTP_TOKEN / minted ac1.* without project-profile bootstrap.
    if not http_headers and settings.prefer_http and http_url and settings.api_token:
        http_headers = {
            "Authorization": f"Bearer {settings.api_token}",
            "X-Tenant-Id": settings.tenant,
            "X-Workspace-Id": settings.workspace,
            "X-Project-Id": settings.project,
            "X-Usage-Profile": settings.usage_profile,
        }

    # --- Local stdio (dogfood same checkout) ---
    if settings.local and not (settings.prefer_http and http_url and http_headers):
        project_state: Path | None = None
        if settings.register and not dry_run:
            project_state = _local_register(settings)
        fragment = materialize_local_stdio_fragment(
            tenant=settings.tenant,
            workspace=settings.workspace,
            project_id=settings.project,
            usage_profile=settings.usage_profile,
            root=repo_root(),
        )
        if dry_run:
            print(json.dumps(fragment, indent=2, sort_keys=True))
            return 0
        written = _write_clients(work, fragment, settings)
        notes = ["Transport is local stdio (same-host dogfood; no SSH/HTTP required)"]
        notes.extend(_guidance_connect_notes(_materialize_mcp_first_guidance(work)))
        if _should_ingest(settings) and not dry_run:
            path = settings.source_server_path or str(work)
            code = _local_ingest(settings, path)
            if code != 0:
                print(f"   {ui.warn('!')} sync exited non-zero ({code})", file=sys.stderr)
            else:
                notes.append(f"Ran local sync for {path}")
        _print_connect_summary(
            settings=settings,
            transport="local-stdio",
            project_state=project_state,
            written=written,
            work=work,
            extra_notes=notes,
        )
        return 0

    if settings.prefer_http and http_url and http_headers:
        fragment = materialize_http_mcp_fragment(url=http_url, headers=http_headers)
        if dry_run:
            print(json.dumps(fragment, indent=2, sort_keys=True))
            return 0
        written = _write_clients(work, fragment, settings)
        notes = [f"Transport is Streamable HTTP ({http_url})"]
        notes.extend(_guidance_connect_notes(_materialize_mcp_first_guidance(work)))
        if settings.smoke_test and not mcp_http_smoke(http_url, http_headers):
            print(
                f"   {ui.warn('!')} MCP HTTP smoke (initialize) failed; check serve-http and token",
                file=sys.stderr,
            )
        if _should_ingest(settings):
            if settings.api_url:
                result = api_ingest(settings)
                notes.append(f"Ingest: {json.dumps(result.get('ingest', result), sort_keys=True)}")
            elif settings.ssh:
                code = remote_ingest(settings)
                if code != 0:
                    print(f"   {ui.warn('!')} sync exited non-zero ({code})", file=sys.stderr)
        _print_connect_summary(
            settings=settings,
            transport=f"streamable_http ({http_url})",
            project_state=None,
            written=written,
            work=work,
            extra_notes=notes,
        )
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
            identity_file=settings.ssh_identity or None,
        )

    if settings.smoke_test and not dry_run:
        if (
            doctor_remote(
                settings.ssh,
                settings.remote_root,
                remote_os=settings.remote_os,
                identity_file=settings.ssh_identity or None,
            )
            != 0
        ):
            raise SystemExit("error: remote doctor failed")

    fragment = materialize_ssh_mcp_fragment(
        ssh_target=settings.ssh,
        remote_root=settings.remote_root,
        tenant=settings.tenant,
        workspace=settings.workspace,
        project_id=settings.project,
        remote_os=settings.remote_os,
        identity_file=settings.ssh_identity or None,
    )
    if dry_run:
        print(json.dumps(fragment, indent=2, sort_keys=True))
        return 0
    written = _write_clients(work, fragment, settings)
    notes = [f"Transport is SSH stdio via {settings.ssh}"]
    notes.extend(_guidance_connect_notes(_materialize_mcp_first_guidance(work)))
    if _should_ingest(settings) and not dry_run:
        if settings.api_url:
            result = api_ingest(settings)
            notes.append(f"Ingest: {json.dumps(result.get('ingest', result), sort_keys=True)}")
        else:
            ingest_code = remote_ingest(settings)
            if ingest_code != 0:
                print(f"   {ui.warn('!')} sync exited non-zero ({ingest_code})", file=sys.stderr)
    _print_connect_summary(
        settings=settings,
        transport="ssh-stdio",
        project_state=None,
        written=written,
        work=work,
        extra_notes=notes,
    )
    return 0
