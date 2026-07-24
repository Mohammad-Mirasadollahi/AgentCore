"""Tests for local (same-host) MCP connect fragment."""

from __future__ import annotations

import json
from pathlib import Path

from agentcore_cli.connect_config import load_connect_settings
from agentcore_cli.local_mcp import materialize_local_stdio_fragment


def test_load_connect_settings_local_without_ssh(tmp_path: Path, monkeypatch):
    cfg = tmp_path / "connect.json"
    cfg.write_text(
        json.dumps(
            {
                "server": {"local": True, "remote_root": "/opt/AgentCore"},
                "scope": {"tenant": "agentcore", "workspace": "dev", "project": "AgentCore"},
                "connect": {"prefer_http": False},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    settings = load_connect_settings(config_path=str(cfg))
    assert settings.local is True
    assert settings.ssh == ""
    assert settings.project == "AgentCore"


def test_settings_for_local_uses_identity_scope(tmp_path: Path, monkeypatch):
    from argparse import Namespace

    from agentcore_cli.commands.connect import _settings_for_local

    monkeypatch.setattr("agentcore_cli.cli_defaults.load_dotenv_files", lambda **_: [])
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_connect_scope", lambda: {})
    monkeypatch.setattr(
        "agentcore_cli.cli_defaults.peek_identity_scope",
        lambda: {"tenant": "acme", "workspace": "eng", "project": "payments"},
    )
    monkeypatch.delenv("AGENTCORE_TENANT_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_WORKSPACE_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_PROJECT_ID", raising=False)
    monkeypatch.chdir(tmp_path)
    args = Namespace(
        tenant="",
        workspace="",
        project="",
        remote_root="",
        clients="all",
        include_user_clients=False,
    )
    settings = _settings_for_local(args, work=tmp_path)
    assert settings.tenant == "acme"
    assert settings.workspace == "eng"
    assert settings.project == "payments"
    assert settings.local is True
