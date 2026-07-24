"""Tests for connect config loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentcore_cli.connect_config import load_connect_settings, write_connect_template


def test_load_connect_settings_from_json(tmp_path: Path, monkeypatch):
    cfg = tmp_path / "connect.json"
    cfg.write_text(
        json.dumps(
            {
                "server": {"ssh": "u@host", "remote_root": "/opt/AgentCore"},
                "scope": {"tenant": "t", "workspace": "w", "project": "p"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    settings = load_connect_settings(config_path=str(cfg))
    assert settings.ssh == "u@host"
    assert settings.project == "p"


def test_project_defaults_to_cwd_name(tmp_path: Path, monkeypatch):
    cfg = tmp_path / "connect.json"
    cfg.write_text(
        json.dumps({"server": {"ssh": "u@host"}, "scope": {"tenant": "t", "workspace": "w"}}),
        encoding="utf-8",
    )
    app = tmp_path / "myapp"
    app.mkdir()
    monkeypatch.chdir(app)
    settings = load_connect_settings(config_path=str(cfg))
    assert settings.project == "myapp"


def test_write_connect_template(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)
    path = write_connect_template()
    assert path == tmp_path / ".agentcore" / "connect.yaml"
    assert path.is_file()
    assert "server:" in path.read_text(encoding="utf-8")


def test_default_config_paths_prefer_repo(tmp_path: Path, monkeypatch):
    from agentcore_cli.connect_config import default_config_paths, default_connect_yaml_path

    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    paths = default_config_paths()
    assert paths[0] == default_connect_yaml_path()
    assert paths[0] == tmp_path / ".agentcore" / "connect.yaml"
    assert any(p == home / ".agentcore" / "connect.yaml" for p in paths)


def test_write_or_merge_connect_yaml_creates_file(tmp_path: Path):
    from agentcore_cli.connect_config import ConnectSettings, write_or_merge_connect_yaml

    path = tmp_path / "connect.yaml"
    settings = ConnectSettings(
        ssh="ops@host",
        remote_root="/opt/AgentCore",
        ssh_identity=str(tmp_path / "key"),
        tenant="t",
        workspace="w",
        project="p",
        prefer_http=False,
    )
    write_or_merge_connect_yaml(settings, path=path, prefer_http=False)
    text = path.read_text(encoding="utf-8")
    assert "ops@host" in text
    assert "prefer_http: false" in text


def test_write_connect_template_refuses_overwrite(tmp_path: Path, monkeypatch):
    target = tmp_path / ".agentcore" / "connect.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("existing", encoding="utf-8")
    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)
    with pytest.raises(SystemExit):
        write_connect_template()


def test_default_identity_path_under_repo(tmp_path: Path, monkeypatch):
    from agentcore_cli.ssh_bootstrap import default_identity_path

    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)
    assert default_identity_path() == tmp_path / ".agentcore" / "ssh" / "id_ed25519_agentcore"
