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


def test_source_path_for_connect_remote_does_not_use_client_cwd(tmp_path: Path):
    from agentcore_cli.commands.connect import _source_path_for_connect

    assert _source_path_for_connect(local=False, work=tmp_path) == ""
    assert _source_path_for_connect(local=True, work=tmp_path) == str(tmp_path)
    assert (
        _source_path_for_connect(
            local=False,
            work=tmp_path,
            configured="/srv/repos/MyApp",
        )
        == "/srv/repos/MyApp"
    )


def test_ensure_remote_source_path_autodetects_when_on_server(tmp_path: Path, monkeypatch):
    from agentcore_cli.commands.connect import _ensure_remote_source_path
    from agentcore_cli.connect_config import ConnectSettings

    monkeypatch.setattr(
        "agentcore_cli.connect_flow.ssh.remote_is_dir",
        lambda _settings, path: path == str(tmp_path.resolve()),
    )
    settings = ConnectSettings(ssh="user@host", source_server_path="")
    out = _ensure_remote_source_path(settings, tmp_path, allow_prompt=False)
    assert out.source_server_path == str(tmp_path.resolve())


def test_ensure_remote_source_path_discovers_opt_project(tmp_path: Path, monkeypatch):
    from agentcore_cli.commands.connect import _ensure_remote_source_path
    from agentcore_cli.connect_config import ConnectSettings

    app = tmp_path / "ThinkingSOC"
    app.mkdir()

    def fake_remote_is_dir(_settings, path: str) -> bool:
        return path == "/opt/ThinkingSOC"

    monkeypatch.setattr("agentcore_cli.connect_flow.ssh.remote_is_dir", fake_remote_is_dir)
    monkeypatch.setattr(
        "agentcore_cli.install_root_marker.discover_remote_install_root",
        lambda *a, **k: Path("/opt/AgentCore"),
    )
    settings = ConnectSettings(ssh="user@host", source_server_path="", remote_root="/opt/AgentCore")
    out = _ensure_remote_source_path(settings, app, allow_prompt=False)
    assert out.source_server_path == "/opt/ThinkingSOC"


def test_ensure_remote_source_path_uses_remote_root_for_agentcore_dogfood(
    tmp_path: Path, monkeypatch
):
    from agentcore_cli.commands.connect import _ensure_remote_source_path
    from agentcore_cli.connect_config import ConnectSettings

    root = tmp_path / "AgentCore"
    (root / "backend" / "packages" / "agentcore_cli").mkdir(parents=True)
    (root / "pyproject.toml").write_text('name = "agentcore"\n', encoding="utf-8")

    def fake_remote_is_dir(_settings, path: str) -> bool:
        return path == "/opt/AgentCore"

    monkeypatch.setattr("agentcore_cli.connect_flow.ssh.remote_is_dir", fake_remote_is_dir)
    monkeypatch.setattr(
        "agentcore_cli.install_root_marker.discover_remote_install_root",
        lambda *a, **k: Path("/opt/AgentCore"),
    )
    monkeypatch.setattr(
        "agentcore_cli.install_root_marker.looks_like_agentcore_root",
        lambda p: Path(p).name == "AgentCore",
    )
    settings = ConnectSettings(ssh="user@host", source_server_path="", remote_root="/opt/AgentCore")
    out = _ensure_remote_source_path(settings, root, allow_prompt=False)
    assert out.source_server_path == "/opt/AgentCore"


def test_ensure_remote_source_path_fails_closed_when_undiscoverable(tmp_path: Path, monkeypatch):
    from agentcore_cli.commands.connect import _ensure_remote_source_path
    from agentcore_cli.connect_config import ConnectSettings

    monkeypatch.setattr("agentcore_cli.connect_flow.ssh.remote_is_dir", lambda *_a, **_k: False)
    monkeypatch.setattr(
        "agentcore_cli.install_root_marker.discover_remote_install_root",
        lambda *a, **k: Path("/opt/AgentCore"),
    )
    settings = ConnectSettings(ssh="user@host", source_server_path="")
    try:
        _ensure_remote_source_path(settings, tmp_path, allow_prompt=True)
        raised = False
    except SystemExit as exc:
        raised = True
        assert "auto-discover source.server_path" in str(exc)
        assert "Probed via SSH" in str(exc)
    assert raised
