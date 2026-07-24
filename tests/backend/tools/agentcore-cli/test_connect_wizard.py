"""Unit tests for interactive SSH connect wizard and yaml merge."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agentcore_cli.connect_config import ConnectSettings, load_connect_settings, write_or_merge_connect_yaml
from agentcore_cli.connect_wizard import ensure_ssh_ready, parse_ssh_target, run_ssh_connect_wizard
from agentcore_cli.parser import build_parser
from agentcore_cli.ssh_bootstrap import IdentityResult


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
            ssh="ops@h",
            tenant="t",
            workspace="w",
            project=work.name,
            source_server_path=str(work),
            prefer_http=False,
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
        ssh="",
        server="",
        clients="all",
        include_user_clients=False,
        tenant="",
        workspace="",
        remote_root="",
    )
    assert cmd_connect(args) == 0
    assert saw_shared == [False, True]


def test_parse_ssh_target():
    assert parse_ssh_target("ops@host.example") == ("ops", "host.example")
    assert parse_ssh_target("host.example") == ("", "host.example")


def test_write_or_merge_preserves_hand_tuned_fields(tmp_path: Path):
    path = tmp_path / "connect.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "server": {"ssh": "old@host", "remote_root": "/opt/AgentCore"},
                "scope": {"tenant": "acme", "workspace": "eng"},
                "clients": "cursor",
                "source": {"server_path": "/srv/repos/App"},
                "connect": {"ingest": "always", "prefer_http": True},
            }
        ),
        encoding="utf-8",
    )
    settings = ConnectSettings(
        ssh="ops@newhost",
        remote_root="/opt/AgentCore",
        ssh_identity=str(tmp_path / "id_ed25519_agentcore"),
        tenant="acme",
        workspace="eng",
        project="App",
        prefer_http=False,
        clients="cursor",
        ingest_mode="always",
    )
    write_or_merge_connect_yaml(settings, path=path, prefer_http=False)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert doc["server"]["ssh"] == "ops@newhost"
    assert doc["auth"]["ssh_key"] == str(tmp_path / "id_ed25519_agentcore")
    assert doc["source"]["server_path"] == "/srv/repos/App"
    assert doc["clients"] == "cursor"
    assert doc["connect"]["prefer_http"] is False
    assert "password" not in doc.get("auth", {})


def test_write_or_merge_never_keeps_password(tmp_path: Path):
    path = tmp_path / "connect.yaml"
    path.write_text(
        yaml.safe_dump({"server": {"ssh": "u@h"}, "auth": {"password": "nope"}}),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="do not store"):
        write_or_merge_connect_yaml(
            ConnectSettings(ssh="u@h", ssh_identity="/tmp/k"),
            path=path,
            prefer_http=False,
        )


def test_run_ssh_connect_wizard_writes_yaml(tmp_path: Path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    identity = home / ".ssh" / "id_ed25519_agentcore"
    identity.parent.mkdir(parents=True)
    identity.write_text("PRIVATE", encoding="utf-8")
    (home / ".ssh" / "id_ed25519_agentcore.pub").write_text(
        "ssh-ed25519 AAAA agentcore-connect\n", encoding="utf-8"
    )

    answers = iter(["agentcore.example", "ops", "acme", "eng", "programming-cursor-mcp"])

    def fake_input(prompt: str) -> str:
        return next(answers)

    def fake_password(prompt: str) -> str:
        return "once-only"

    def fake_bootstrap(ssh_target, password, *, rotate=False, identity=None):
        assert ssh_target == "ops@agentcore.example"
        assert password == "once-only"
        assert rotate is True
        return IdentityResult(
            private_path=identity,
            public_path=Path(f"{identity}.pub"),
            old_public_line="ssh-ed25519 OLD",
        )

    monkeypatch.setattr("agentcore_cli.connect_wizard.bootstrap_ssh_auth", fake_bootstrap)
    monkeypatch.setattr("agentcore_cli.connect_wizard._require_tty", lambda: None)
    monkeypatch.setattr(
        "agentcore_cli.install_root_marker.discover_remote_install_root",
        lambda *a, **k: Path("/opt/AgentCore"),
    )

    app = tmp_path / "MyApp"
    app.mkdir()
    settings = run_ssh_connect_wizard(
        existing=ConnectSettings(project="MyApp"),
        rotate=True,
        config_path=home / ".agentcore" / "connect.yaml",
        project_dir=app,
        input_fn=fake_input,
        password_fn=fake_password,
    )
    assert settings.ssh == "ops@agentcore.example"
    assert settings.remote_root == "/opt/AgentCore"
    assert settings.usage_profile == "programming-cursor-mcp"
    assert settings.prefer_http is False
    cfg = (home / ".agentcore" / "connect.yaml").read_text(encoding="utf-8")
    assert "ops@agentcore.example" in cfg
    assert "once-only" not in cfg
    assert "password" not in cfg


def test_run_ssh_connect_wizard_fails_when_discover_misses(tmp_path: Path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    identity = home / ".ssh" / "id_ed25519_agentcore"
    identity.parent.mkdir(parents=True)
    identity.write_text("PRIVATE", encoding="utf-8")
    (home / ".ssh" / "id_ed25519_agentcore.pub").write_text(
        "ssh-ed25519 AAAA agentcore-connect\n", encoding="utf-8"
    )
    answers = iter(["h.example", "ops", "t", "w", "default"])

    def fake_input(prompt: str) -> str:
        return next(answers)

    monkeypatch.setattr(
        "agentcore_cli.connect_wizard.bootstrap_ssh_auth",
        lambda *a, **k: IdentityResult(private_path=identity, public_path=Path(f"{identity}.pub")),
    )
    monkeypatch.setattr("agentcore_cli.connect_wizard._require_tty", lambda: None)
    monkeypatch.setattr(
        "agentcore_cli.install_root_marker.discover_remote_install_root",
        lambda *a, **k: None,
    )
    app = tmp_path / "App"
    app.mkdir()
    with pytest.raises(SystemExit, match="install-root marker"):
        run_ssh_connect_wizard(
            existing=ConnectSettings(project="App"),
            rotate=False,
            config_path=home / "connect.yaml",
            project_dir=app,
            input_fn=fake_input,
            password_fn=lambda _p: "pw",
        )


def test_ensure_ssh_ready_batch_fail_starts_wizard(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("agentcore_cli.connect_wizard.probe_batch_mode", lambda *a, **k: False)
    monkeypatch.setattr("agentcore_cli.connect_wizard.sys.stdin.isatty", lambda: True)

    def fake_wizard(*, existing, rotate, **kwargs):
        assert rotate is True
        return ConnectSettings(ssh="ops@host", ssh_identity="/tmp/k", prefer_http=False)

    monkeypatch.setattr("agentcore_cli.connect_wizard.run_ssh_connect_wizard", fake_wizard)
    out = ensure_ssh_ready(
        ConnectSettings(ssh="ops@host", prefer_http=False, mcp_http_url="", api_token=""),
        allow_wizard=True,
    )
    assert out.ssh_identity == "/tmp/k"


def test_prompt_usage_profile_accepts_number(monkeypatch):
    from agentcore_cli.connect_wizard import prompt_usage_profile

    monkeypatch.setattr(
        "usage_profile.list_profile_ids",
        lambda: ["default", "programming-cursor-mcp"],
    )
    monkeypatch.setattr(
        "usage_profile.load_usage_profile",
        lambda pid: {"title": pid},
    )
    assert prompt_usage_profile(input_fn=lambda _p: "2") == "programming-cursor-mcp"
    assert prompt_usage_profile(default="default", input_fn=lambda _p: "") == "default"


def test_ensure_ssh_ready_edit_rotates(tmp_path: Path, monkeypatch):
    called: dict[str, bool] = {}

    def fake_wizard(*, existing, rotate, **kwargs):
        called["rotate"] = rotate
        return ConnectSettings(ssh="ops@h", ssh_identity="/tmp/k", prefer_http=False)

    monkeypatch.setattr("agentcore_cli.connect_wizard.run_ssh_connect_wizard", fake_wizard)
    out = ensure_ssh_ready(ConnectSettings(ssh="old@h"), force_edit=True, allow_wizard=True)
    assert called["rotate"] is True
    assert out.ssh == "ops@h"


def test_ensure_ssh_ready_batch_fail_non_tty(monkeypatch):
    monkeypatch.setattr("agentcore_cli.connect_wizard.probe_batch_mode", lambda *a, **k: False)
    monkeypatch.setattr("agentcore_cli.connect_wizard.sys.stdin.isatty", lambda: False)
    with pytest.raises(SystemExit, match="connect edit"):
        ensure_ssh_ready(
            ConnectSettings(ssh="ops@host", prefer_http=False, mcp_http_url="", api_token=""),
            allow_wizard=True,
        )


def test_load_allow_incomplete(tmp_path: Path):
    cfg = tmp_path / "connect.yaml"
    cfg.write_text(yaml.safe_dump({"scope": {"tenant": "t", "workspace": "w"}}), encoding="utf-8")
    settings = load_connect_settings(config_path=str(cfg), allow_incomplete=True)
    assert settings.tenant == "t"
    with pytest.raises(SystemExit, match="server.local"):
        load_connect_settings(config_path=str(cfg), allow_incomplete=False)
