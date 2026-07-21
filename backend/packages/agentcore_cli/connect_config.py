"""Load ~/.agentcore/connect.yaml (or .json) for `agentcore connect`."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from agentcore_cli.connect_security import harden_connect_config_permissions, reject_secrets_in_connect_doc


@dataclass
class ConnectSettings:
    """Resolved connect configuration after file + env merge."""

    ssh: str = ""
    remote_root: str = "/opt/AgentCore"
    api_url: str = ""
    api_token: str = ""
    ssh_identity: str = ""
    tenant: str = "default"
    workspace: str = "default"
    project: str = ""
    project_name: str = ""
    usage_profile: str = "programming-cursor-mcp"
    clients: str = "all"
    include_user_clients: bool = False
    register: bool = True
    smoke_test: bool = True
    ingest_mode: str = "optional"
    source_server_path: str = ""
    source_git_remote: str = ""
    source_git_branch: str = "main"
    mcp_http_url: str = ""
    prefer_http: bool = True
    local: bool = False
    remote_os: str = "unix"
    actor_id: str = "connect-cli"


def default_config_paths() -> list[Path]:
    base = Path.home() / ".agentcore"
    return [
        base / "connect.yaml",
        base / "connect.yml",
        base / "connect.json",
    ]


def resolve_config_path(explicit: str = "") -> Path:
    if explicit.strip():
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise SystemExit(f"error: connect config not found: {path}")
        return path
    for candidate in default_config_paths():
        if candidate.is_file():
            return candidate
    raise SystemExit(
        "error: no connect config; run `agentcore connect --init` or create ~/.agentcore/connect.yaml"
    )


def _read_config_file(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
    else:
        data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"error: connect config root must be a mapping: {path}")
    return data


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def load_connect_settings(
    *,
    config_path: str = "",
    project_override: str = "",
    ssh_override: str = "",
    api_url_override: str = "",
    clients_override: str = "",
    cwd: Path | None = None,
) -> ConnectSettings:
    path = resolve_config_path(config_path)
    doc = _read_config_file(path)
    reject_secrets_in_connect_doc(doc, path)
    server = doc.get("server") or {}
    auth = doc.get("auth") or {}
    scope = doc.get("scope") or {}
    source = doc.get("source") or {}
    connect = doc.get("connect") or {}

    token_env = str(auth.get("token_env") or "AGENTCORE_TOKEN")
    token = _env(token_env) or str(auth.get("token") or "")

    settings = ConnectSettings(
        ssh=str(server.get("ssh") or "").strip(),
        remote_root=str(server.get("remote_root") or "/opt/AgentCore").strip(),
        api_url=str(server.get("url") or "").strip().rstrip("/"),
        api_token=token,
        ssh_identity=str(auth.get("ssh_key") or "").strip(),
        tenant=str(scope.get("tenant") or "default").strip(),
        workspace=str(scope.get("workspace") or "default").strip(),
        project=str(scope.get("project") or "").strip(),
        project_name=str(scope.get("name") or scope.get("project_name") or "").strip(),
        usage_profile=str(doc.get("usage_profile") or "programming-cursor-mcp").strip(),
        clients=str(doc.get("clients") or "all").strip(),
        include_user_clients=bool(doc.get("include_user_clients")),
        register=bool(connect.get("register", True)),
        smoke_test=bool(connect.get("smoke_test", True)),
        ingest_mode=str(connect.get("ingest") or "optional").strip().lower(),
        source_server_path=str(source.get("server_path") or "").strip(),
        source_git_remote=str((source.get("git") or {}).get("remote") or "").strip()
        if isinstance(source.get("git"), dict)
        else str(source.get("git_remote") or "").strip(),
        source_git_branch=str((source.get("git") or {}).get("branch") or "main").strip()
        if isinstance(source.get("git"), dict)
        else "main",
        mcp_http_url=str(server.get("mcp_http_url") or "").strip().rstrip("/"),
        prefer_http=bool(connect.get("prefer_http", True)),
        local=bool(server.get("local") or connect.get("local")),
        remote_os=str(server.get("remote_os") or "unix").strip(),
        actor_id=str(doc.get("actor_id") or "connect-cli").strip(),
    )

    settings.ssh = _env("AGENTCORE_CONNECT_SSH", settings.ssh) or _env("AGENTCORE_SSH", settings.ssh)
    settings.remote_root = _env("AGENTCORE_CONNECT_REMOTE_ROOT", settings.remote_root)
    settings.api_url = _env("AGENTCORE_CONNECT_URL", settings.api_url)
    settings.api_token = _env("AGENTCORE_CONNECT_TOKEN", settings.api_token) or settings.api_token
    settings.tenant = _env("AGENTCORE_CONNECT_TENANT", settings.tenant)
    settings.workspace = _env("AGENTCORE_CONNECT_WORKSPACE", settings.workspace)
    settings.project = _env("AGENTCORE_CONNECT_PROJECT", settings.project)
    settings.ssh_identity = _env("AGENTCORE_CONNECT_SSH_KEY", settings.ssh_identity)
    settings.mcp_http_url = _env("AGENTCORE_CONNECT_MCP_HTTP_URL", settings.mcp_http_url)
    if _env("AGENTCORE_CONNECT_LOCAL", "").lower() in ("1", "true", "yes"):
        settings.local = True

    if ssh_override.strip():
        settings.ssh = ssh_override.strip()
    if api_url_override.strip():
        settings.api_url = api_url_override.strip().rstrip("/")
    if clients_override.strip():
        settings.clients = clients_override.strip()

    work = cwd or Path.cwd()
    if project_override.strip():
        settings.project = project_override.strip()
    elif not settings.project:
        settings.project = work.name or "project"

    if not settings.project_name:
        settings.project_name = settings.project

    if (
        not settings.local
        and not settings.ssh
        and not settings.api_url
        and not settings.mcp_http_url
    ):
        raise SystemExit(
            "error: set server.local: true, and/or server.ssh, and/or server.url / mcp_http_url"
        )
    return settings


CONNECT_TEMPLATE = """# AgentCore connect — see docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md
#
# Replace example hostnames/paths with yours. Do not store OS or DB passwords here.
#
# --- Local mode (same machine: dogfood AgentCore on its own checkout) ---
# server:
#   local: true
#   remote_root: /opt/AgentCore
# connect:
#   prefer_http: false
#
# --- SSH mode (private LAN, recommended without TLS) ---
# server:
#   ssh: ops@agentcore.example.internal
#   remote_root: /opt/AgentCore
# auth:
#   ssh_key: ~/.ssh/id_ed25519_agentcore
# connect:
#   prefer_http: false
#
# --- HTTP mode (requires: agentcore mcp serve-http on the AgentCore host) ---
server:
  url: http://agentcore.example.internal:32194
  mcp_http_url: http://agentcore.example.internal:32500
  # Optional SSH fallback:
  # ssh: ops@agentcore.example.internal
  # remote_root: /opt/AgentCore

auth:
  token_env: AGENTCORE_TOKEN
  # ssh_key: ~/.ssh/id_ed25519_agentcore

scope:
  tenant: acme
  workspace: eng
  # project: defaults to current directory name

usage_profile: programming-cursor-mcp
clients: all

source:
  server_path: /srv/repos/MyApp

connect:
  register: true
  smoke_test: true
  prefer_http: true
  ingest: optional
"""


def write_connect_template(path: Path | None = None) -> Path:
    target = path or (Path.home() / ".agentcore" / "connect.yaml")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        raise SystemExit(f"error: refusing to overwrite existing {target}")
    target.write_text(CONNECT_TEMPLATE, encoding="utf-8")
    harden_connect_config_permissions(target)
    return target
