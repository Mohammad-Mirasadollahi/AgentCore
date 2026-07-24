"""Load connect.yaml from the app checkout ``.agentcore/`` (client-local).

Primary path: ``<project-cwd>/.agentcore/connect.yaml``.
Fallback: AgentCore install ``.agentcore/``, then legacy ``~/.agentcore/``.
"""

from __future__ import annotations

import json
import os
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
    usage_profile: str = ""
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


def repo_agentcore_dir(root: Path | None = None) -> Path:
    """Checkout-local AgentCore state dir (``<repo>/.agentcore``)."""
    from agentcore_cli.util import repo_root

    return (root or repo_root()) / ".agentcore"


def project_agentcore_dir(project_root: Path | None = None) -> Path:
    """App-checkout state dir: ``<project>/.agentcore`` (defaults to cwd)."""
    return (project_root or Path.cwd()).resolve() / ".agentcore"


def default_connect_yaml_path(root: Path | None = None) -> Path:
    """Canonical write target: project checkout ``.agentcore/connect.yaml`` (cwd when omitted)."""
    return project_agentcore_dir(root) / "connect.yaml"


def default_config_paths(root: Path | None = None) -> list[Path]:
    """Resolve order: project checkout → AgentCore install → legacy ``~/.agentcore/``."""
    from agentcore_cli.util import repo_root

    project_base = project_agentcore_dir(root)
    install_base = repo_agentcore_dir()
    home_base = Path.home() / ".agentcore"
    bases: list[Path] = []
    for base in (project_base, install_base, home_base):
        if base not in bases:
            bases.append(base)
    out: list[Path] = []
    for base in bases:
        out.extend(
            [
                base / "connect.yaml",
                base / "connect.yml",
                base / "connect.json",
            ]
        )
    return out


def resolve_config_path(explicit: str = "", *, project_root: Path | None = None) -> Path:
    if explicit.strip():
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise SystemExit(f"error: connect config not found: {path}")
        return path
    for candidate in default_config_paths(project_root):
        if candidate.is_file():
            return candidate
    hint = default_connect_yaml_path(project_root)
    raise SystemExit(
        f"error: no connect config; run `agentcore connect init` or create {hint}"
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
    allow_incomplete: bool = False,
    project_root: Path | None = None,
) -> ConnectSettings:
    work = cwd or project_root or Path.cwd()
    path = resolve_config_path(config_path, project_root=work)
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
        usage_profile=str(doc.get("usage_profile") or "").strip(),
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

    if project_override.strip():
        settings.project = project_override.strip()
    elif not settings.project:
        settings.project = work.name or "project"

    if not settings.project_name:
        settings.project_name = settings.project

    if (
        not allow_incomplete
        and not settings.local
        and not settings.ssh
        and not settings.api_url
        and not settings.mcp_http_url
    ):
        raise SystemExit(
            "error: set server.local: true, and/or server.ssh, and/or server.url / mcp_http_url "
            "(or run `agentcore connect` / `agentcore connect edit` in a TTY)"
        )
    return settings


CONNECT_TEMPLATE = """# AgentCore connect — see docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md
#
# Lives under this checkout: .agentcore/connect.yaml (gitignored).
# Preferred first-time path: run `agentcore connect` in a TTY (interactive SSH wizard).
# Re-auth / replace pubkey: `agentcore connect edit`
# Multi-project: `agentcore connect /path/a,/path/b` (comma-separated; pins all for sync)
# Hand-edit this file for scope/clients/remote_root. If server.ssh or auth.ssh_key
# breaks BatchMode login, run `agentcore connect edit` (do not store OS passwords here).
# Sync uses the project dir(s) you connected (pinned software paths).
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
#   ssh_key: .agentcore/ssh/id_ed25519_agentcore
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
  # ssh_key: .agentcore/ssh/id_ed25519_agentcore

scope:
  tenant: acme
  workspace: eng
  # project: defaults to current directory name

# usage_profile is chosen during `agentcore connect` (not at client install time)
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
    target = path or default_connect_yaml_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        raise SystemExit(f"error: refusing to overwrite existing {target}")
    target.write_text(CONNECT_TEMPLATE, encoding="utf-8")
    harden_connect_config_permissions(target)
    return target


def _ensure_mapping(doc: dict[str, Any], key: str) -> dict[str, Any]:
    raw = doc.get(key)
    if isinstance(raw, dict):
        return raw
    nested: dict[str, Any] = {}
    doc[key] = nested
    return nested


def write_or_merge_connect_yaml(
    settings: ConnectSettings,
    *,
    path: Path | None = None,
    prefer_http: bool | None = None,
) -> Path:
    """Create or merge SSH/wizard fields into connect.yaml without wiping hand-tuned keys."""
    target = path or default_connect_yaml_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    doc: dict[str, Any] = {}
    if target.is_file():
        doc = _read_config_file(target)
        reject_secrets_in_connect_doc(doc, target)

    server = _ensure_mapping(doc, "server")
    auth = _ensure_mapping(doc, "auth")
    scope = _ensure_mapping(doc, "scope")
    connect = _ensure_mapping(doc, "connect")

    if settings.ssh:
        server["ssh"] = settings.ssh
    if settings.remote_root:
        server["remote_root"] = settings.remote_root
    if settings.local:
        server["local"] = True
    elif "local" in server and not settings.local:
        server.pop("local", None)

    if settings.ssh_identity:
        auth["ssh_key"] = settings.ssh_identity
    # Never persist password; strip if a previous bad edit left one.
    for forbidden in ("password", "postgres_password", "neo4j_password", "secret"):
        auth.pop(forbidden, None)

    if settings.tenant:
        scope["tenant"] = settings.tenant
    if settings.workspace:
        scope["workspace"] = settings.workspace
    if settings.project:
        scope["project"] = settings.project
    if settings.project_name and settings.project_name != settings.project:
        scope["name"] = settings.project_name

    if settings.usage_profile:
        doc["usage_profile"] = settings.usage_profile
    if settings.clients:
        doc["clients"] = settings.clients

    connect["register"] = settings.register
    connect["smoke_test"] = settings.smoke_test
    http_pref = settings.prefer_http if prefer_http is None else prefer_http
    connect["prefer_http"] = bool(http_pref)
    if settings.ingest_mode:
        connect["ingest"] = settings.ingest_mode

    if settings.source_server_path:
        source = _ensure_mapping(doc, "source")
        source["server_path"] = settings.source_server_path

    from agentcore_cli.connect_security import atomic_write_text

    body = yaml.safe_dump(doc, default_flow_style=False, sort_keys=False, allow_unicode=True)
    atomic_write_text(target, body if body.endswith("\n") else body + "\n", mode=0o600)
    harden_connect_config_permissions(target)
    return target


def try_resolve_config_path(
    explicit: str = "",
    *,
    project_root: Path | None = None,
) -> Path | None:
    """Like resolve_config_path but returns None when missing (for wizard entry)."""
    if explicit.strip():
        path = Path(explicit).expanduser()
        return path if path.is_file() else None
    for candidate in default_config_paths(project_root):
        if candidate.is_file():
            return candidate
    return None
