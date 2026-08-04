"""Unit tests for the interactive HTTPS connect wizard and yaml merge (SSH removed)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agentcore_cli.connect_config import ConnectSettings, load_connect_settings, write_or_merge_connect_yaml
from agentcore_cli.parser import build_parser


def test_connect_parser_word_modes():
    parser = build_parser()
    assert parser.parse_args(["connect"]).connect_mode == ""
    assert parser.parse_args(["connect", "edit"]).connect_mode == "edit"
    assert parser.parse_args(["connect", "init"]).connect_mode == "init"
    assert parser.parse_args(["connect", "/a,/b"]).connect_mode == "/a,/b"


def test_parse_connect_project_dirs(tmp_path: Path):
    from agentcore_cli.commands.connect import parse_connect_project_dirs

    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    assert parse_connect_project_dirs("", cwd=tmp_path) == [tmp_path.resolve()]
    assert parse_connect_project_dirs(f"{a},{b}", cwd=tmp_path) == [a.resolve(), b.resolve()]
    with pytest.raises(SystemExit, match="not a directory"):
        parse_connect_project_dirs(str(tmp_path / "missing"), cwd=tmp_path)


def test_cmd_connect_multi_path_reuses_shared_settings(tmp_path: Path, monkeypatch):
    from argparse import Namespace
    from dataclasses import replace

    from agentcore_cli.commands.connect import cmd_connect
    from agentcore_cli.connect_config import ConnectSettings

    a = tmp_path / "AppA"
    b = tmp_path / "AppB"
    a.mkdir()
    b.mkdir()
    saw_shared: list[bool] = []

    def fake_one(args, *, work, shared, force_edit):
        saw_shared.append(shared is not None)
        settings = shared or ConnectSettings(
            api_url="https://agentcore.example",
            tenant="t",
            workspace="w",
            project=work.name,
            source_server_path=str(work),
            prefer_http=True,
            local=False,
        )
        return 0, replace(settings, project=work.name, source_server_path=str(work))

    monkeypatch.setattr("agentcore_cli.commands.connect._connect_one", fake_one)
    monkeypatch.setattr("agentcore_cli.commands.connect._pin_software_paths", lambda *a, **k: None)
    monkeypatch.chdir(tmp_path)
    args = Namespace(
        connect_mode=f"{a},{b}",
        config="",
        local=False,
        dry_run=True,
        project="",
        server="",
        clients="all",
        include_user_clients=False,
        tenant="",
        workspace="",
        remote_root="",
    )
    assert cmd_connect(args) == 0
    assert saw_shared == [False, True]


def test_write_or_merge_preserves_hand_tuned_fields(tmp_path: Path):
    path = tmp_path / "connect.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "server": {"url": "https://old.example", "remote_root": "/opt/AgentCore"},
                "scope": {"tenant": "acme", "workspace": "eng"},
                "clients": "cursor",
                "source": {"server_path": "/srv/repos/App"},
                "connect": {"ingest": "always", "prefer_http": True},
            }
        ),
        encoding="utf-8",
    )
    settings = ConnectSettings(
        api_url="https://new.example",
        remote_root="/opt/AgentCore",
        tenant="acme",
        workspace="eng",
        project="App",
        prefer_http=True,
        clients="cursor",
        ingest_mode="always",
    )
    write_or_merge_connect_yaml(settings, path=path, prefer_http=True)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert doc["server"]["url"] == "https://new.example"
    assert doc["source"]["server_path"] == "/srv/repos/App"
    assert doc["clients"] == "cursor"
    assert doc["connect"]["prefer_http"] is True
    assert "password" not in doc.get("auth", {})


def test_write_or_merge_strips_legacy_ssh_keys(tmp_path: Path):
    """Old connect.yaml with server.ssh / auth.ssh_key must not survive a merge."""
    path = tmp_path / "connect.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "server": {"ssh": "old@host", "remote_root": "/opt/AgentCore"},
                "auth": {"ssh_key": "/tmp/id_ed25519_agentcore"},
                "scope": {"tenant": "acme", "workspace": "eng"},
            }
        ),
        encoding="utf-8",
    )
    settings = ConnectSettings(api_url="https://agentcore.example", tenant="acme", workspace="eng", project="App")
    write_or_merge_connect_yaml(settings, path=path, prefer_http=True)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "ssh" not in doc.get("server", {})
    assert "ssh_key" not in doc.get("auth", {})
    assert doc["server"]["url"] == "https://agentcore.example"


def test_write_or_merge_never_keeps_password(tmp_path: Path):
    path = tmp_path / "connect.yaml"
    path.write_text(
        yaml.safe_dump({"server": {"url": "https://u.example"}, "auth": {"password": "nope"}}),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="do not store"):
        write_or_merge_connect_yaml(
            ConnectSettings(api_url="https://u.example"),
            path=path,
            prefer_http=True,
        )


def test_run_https_connect_wizard_writes_yaml(tmp_path: Path, monkeypatch):
    from agentcore_cli.connect_wizard import run_https_connect_wizard

    monkeypatch.setattr("agentcore_cli.connect_wizard._require_tty", lambda: None)
    answers = iter(["https://agentcore.example:9443", "acme", "eng"])

    def fake_input(prompt: str) -> str:
        return next(answers)

    def fake_password(prompt: str) -> str:
        return ""

    app = tmp_path / "MyApp"
    app.mkdir()
    cfg_path = tmp_path / ".agentcore" / "connect.yaml"
    settings = run_https_connect_wizard(
        existing=ConnectSettings(project="MyApp", usage_profile="programming-cursor-mcp"),
        config_path=cfg_path,
        project_dir=app,
        input_fn=fake_input,
        password_fn=fake_password,
    )
    assert settings.api_url == "https://agentcore.example:9443"
    assert settings.tenant == "acme"
    assert settings.workspace == "eng"
    assert settings.prefer_http is True

    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert "ssh" not in doc.get("server", {})
    assert "ssh_key" not in doc.get("auth", {})
    assert doc["server"]["url"] == "https://agentcore.example:9443"
    assert not (tmp_path / ".agentcore" / "ssh").exists()


def test_run_https_connect_wizard_rejects_non_https(tmp_path: Path, monkeypatch):
    from agentcore_cli.connect_wizard import run_https_connect_wizard

    monkeypatch.setattr("agentcore_cli.connect_wizard._require_tty", lambda: None)
    answers = iter(["http://agentcore.example:9443"])
    app = tmp_path / "MyApp"
    app.mkdir()
    with pytest.raises(SystemExit, match="https://"):
        run_https_connect_wizard(
            existing=ConnectSettings(project="MyApp"),
            config_path=tmp_path / ".agentcore" / "connect.yaml",
            project_dir=app,
            input_fn=lambda _p: next(answers),
            password_fn=lambda _p: "",
        )


def test_connect_one_runs_https_wizard_when_server_given(tmp_path: Path, monkeypatch):
    """`--server https://…` on a fresh connect wires through the HTTPS wizard."""
    from argparse import Namespace
    from dataclasses import replace

    from agentcore_cli.commands import connect as connect_mod

    monkeypatch.setenv("HOME", str(tmp_path))
    app = tmp_path / "App"
    app.mkdir()
    calls: list[str] = []

    def fake_https_wizard(*, existing, config_path, project_dir, url_override):
        calls.append(url_override)
        return replace(existing, api_url=url_override, prefer_http=True, project="App")

    monkeypatch.setattr(connect_mod, "run_https_connect_wizard", fake_https_wizard)
    monkeypatch.setattr(
        connect_mod,
        "_persist_and_run_connect",
        lambda settings, **_k: (0, settings),
    )
    args = Namespace(
        project="",
        dry_run=True,
        local=False,
        config="",
        clients="all",
        include_user_clients=False,
        tenant="",
        workspace="",
        server="https://agentcore.example:9443",
        usage_profile="programming-cursor-mcp",
    )
    code, settings = connect_mod._connect_one(args, work=app, shared=None, force_edit=False)
    assert code == 0
    assert calls == ["https://agentcore.example:9443"]
    assert settings.api_url == "https://agentcore.example:9443"


def test_prompt_usage_profile_accepts_number(monkeypatch):
    from agentcore_cli.connect_wizard import prompt_usage_profile

    monkeypatch.setattr(
        "usage_profile.list_profile_ids",
        lambda: ["alpha", "programming-cursor-mcp"],
    )
    monkeypatch.setattr(
        "usage_profile.load_usage_profile",
        lambda pid: {"title": pid},
    )
    assert prompt_usage_profile(input_fn=lambda _p: "2") == "programming-cursor-mcp"
    assert prompt_usage_profile(default="alpha", input_fn=lambda _p: "") == "alpha"


def test_prompt_usage_profile_auto_selects_sole_entry(monkeypatch):
    from agentcore_cli.connect_wizard import prompt_usage_profile

    monkeypatch.setattr(
        "usage_profile.list_profile_ids",
        lambda: ["programming-cursor-mcp"],
    )
    assert prompt_usage_profile(input_fn=lambda _p: (_ for _ in ()).throw(AssertionError("no prompt"))) == (
        "programming-cursor-mcp"
    )


def test_load_allow_incomplete(tmp_path: Path):
    cfg = tmp_path / "connect.yaml"
    cfg.write_text(yaml.safe_dump({"scope": {"tenant": "t", "workspace": "w"}}), encoding="utf-8")
    settings = load_connect_settings(config_path=str(cfg), allow_incomplete=True)
    assert settings.tenant == "t"
    with pytest.raises(SystemExit, match="server.local"):
        load_connect_settings(config_path=str(cfg), allow_incomplete=False)
