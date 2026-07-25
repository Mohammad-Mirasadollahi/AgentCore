"""Connect entrypoint: reachability + local / HTTP / SSH transport wiring.

Module contract:
- Role: orchestrate ``agentcore connect`` end-to-end for one project dir.
- SoT / invariants: ``ConnectSettings`` + server API/SSH; prefer HTTP MCP when ready.
- Failures: reachability / doctor / missing transport fail closed. Dry-run never writes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from agentcore_cli import ui
from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.connect_flow.api import api_bootstrap, api_health, api_ingest, mcp_http_smoke
from agentcore_cli.connect_flow.ingest import local_ingest, remote_ingest, should_ingest
from agentcore_cli.connect_flow.ssh import run_ssh
from agentcore_cli.connect_flow.summary import (
    guidance_connect_notes,
    local_register,
    materialize_mcp_first_guidance,
    print_connect_summary,
    write_clients,
)
from agentcore_cli.connect_security import validate_connect_settings
from agentcore_cli.local_mcp import materialize_local_stdio_fragment
from agentcore_cli.mcp_client_targets import materialize_http_mcp_fragment
from agentcore_cli.remote_client import doctor_remote, materialize_ssh_mcp_fragment, remote_register_project
from agentcore_cli.util import repo_root


def reachability_check(settings: ConnectSettings) -> None:
    if settings.local:
        return
    if settings.api_url and not api_health(settings):
        raise SystemExit(f"error: API health check failed for {settings.api_url}/health")
    # Prefer HTTP when URL + token can wire MCP; do not require SSH BatchMode in that case.
    http_ready = bool(settings.prefer_http and settings.mcp_http_url and settings.api_token)
    if settings.ssh and not http_ready and run_ssh(settings, ["true"]) != 0:
        raise SystemExit(
            f"error: SSH reachability failed for {settings.ssh} (BatchMode / key auth). "
            "Run `agentcore connect edit` to re-auth and replace the AgentCore pubkey, "
            "or fix auth.ssh_key in .agentcore/connect.yaml."
        )


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
            project_state = local_register(settings)
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
        written = write_clients(work, fragment, settings)
        notes = ["Transport is local stdio (same-host dogfood; no SSH/HTTP required)"]
        notes.extend(guidance_connect_notes(materialize_mcp_first_guidance(work)))
        if should_ingest(settings) and not dry_run:
            path = settings.source_server_path or str(work)
            code = local_ingest(settings, path)
            if code != 0:
                print(f"   {ui.warn('!')} sync exited non-zero ({code})", file=sys.stderr)
            else:
                notes.append(f"Ran local sync for {path}")
        print_connect_summary(
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
        written = write_clients(work, fragment, settings)
        notes = [f"Transport is Streamable HTTP ({http_url})"]
        notes.extend(guidance_connect_notes(materialize_mcp_first_guidance(work)))
        if settings.smoke_test and not mcp_http_smoke(http_url, http_headers):
            print(
                f"   {ui.warn('!')} MCP HTTP smoke (initialize) failed; check serve-http and token",
                file=sys.stderr,
            )
        if should_ingest(settings):
            if settings.api_url:
                result = api_ingest(settings)
                notes.append(f"Ingest: {json.dumps(result.get('ingest', result), sort_keys=True)}")
            elif settings.ssh:
                code = remote_ingest(settings)
                if code != 0:
                    print(f"   {ui.warn('!')} sync exited non-zero ({code})", file=sys.stderr)
        print_connect_summary(
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
    written = write_clients(work, fragment, settings)
    notes = [f"Transport is SSH stdio via {settings.ssh}"]
    notes.extend(guidance_connect_notes(materialize_mcp_first_guidance(work)))
    if should_ingest(settings) and not dry_run:
        if settings.api_url:
            result = api_ingest(settings)
            notes.append(f"Ingest: {json.dumps(result.get('ingest', result), sort_keys=True)}")
        else:
            ingest_code = remote_ingest(settings)
            if ingest_code != 0:
                print(f"   {ui.warn('!')} sync exited non-zero ({ingest_code})", file=sys.stderr)
    print_connect_summary(
        settings=settings,
        transport="ssh-stdio",
        project_state=None,
        written=written,
        work=work,
        extra_notes=notes,
    )
    return 0
