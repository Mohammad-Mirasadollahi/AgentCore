"""Client checkout sync routes over SSH when Compose stack is absent."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from agentcore_cli.commands import sync as sync_cmd
from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.connect_flow import remote_ingest, remote_sync_from_args


def test_remote_sync_from_args_builds_ssh_command(monkeypatch):
    seen: list[list[str]] = []

    def fake_run(settings, remote_command, *, connect_timeout=15):
        seen.append(list(remote_command))
        return 0

    monkeypatch.setattr("agentcore_cli.connect_flow.remote_sync.run_ssh", fake_run)
    monkeypatch.setattr("agentcore_cli.connect_flow.remote_sync.remote_is_dir", lambda *_a, **_k: True)
    monkeypatch.setattr(
        "agentcore_cli.connect_flow.remote_sync.client_remote_cloud_llm_allowed",
        lambda *_a, **_k: False,
    )
    settings = ConnectSettings(
        ssh="user@host",
        remote_root="/opt/AgentCore",
        tenant="t1",
        workspace="w1",
        project="p1",
        source_server_path="/opt/src",
    )
    args = Namespace(
        tenant=None,
        workspace=None,
        project=None,
        path=None,
        max_files=100,
        force=True,
        allow_cloud_llm=False,
        cpu_percent=None,
        progress_interval=30.0,
        skip_nonconforming=False,
        sync_nonconforming=False,
        exclude_dir=[],
        include_path=[],
        include_ext=[],
    )
    assert remote_sync_from_args(settings, args) == 0
    assert seen
    cmd = seen[0]
    assert cmd[0] == "/opt/AgentCore/.venv/bin/agentcore"
    assert cmd[1] == "sync"
    assert "--path" in cmd and "/opt/src" in cmd
    # Remote argv must use bare max-file (peel_sync_max_file rejects --max-files).
    assert "max-file" in cmd and "100" in cmd
    assert "--max-files" not in cmd and "--max-file" not in cmd
    # sync has no --force; must not forward it or remote parse fails after max-file.
    assert "--force" not in cmd
    assert "--allow-cloud-llm" not in cmd
    from agentcore_cli.parser import build_parser

    parsed = build_parser().parse_args(cmd[1:])
    assert parsed.max_files == 100


def test_remote_sync_prompts_local_cloud_llm_consent_and_forwards_flag(monkeypatch):
    """SSH has no TTY — consent must run locally, then --allow-cloud-llm goes remote."""
    seen: list[list[str]] = []
    prompts: list[str] = []

    monkeypatch.setattr(
        "agentcore_cli.connect_flow.remote_sync.run_ssh",
        lambda settings, remote_command, *, connect_timeout=15: seen.append(list(remote_command)) or 0,
    )
    monkeypatch.setattr("agentcore_cli.connect_flow.remote_sync.remote_is_dir", lambda *_a, **_k: True)
    monkeypatch.setattr(
        "agentcore_cli.connect_flow.remote_sync.remote_llm_config",
        lambda _settings: {
            "enabled": True,
            "api_base": "https://llm.example.com",
            "docs_enabled": True,
            "embeddings_enabled": False,
            "route_docs": {"primary_model": "openai/gpt-oss", "fallback_models": []},
            "route_embed": {"primary_model": "", "fallback_models": []},
        },
    )
    answers = iter(["y", "yes"])

    def fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    import agentcore_cli.commands.graph as graph_mod

    real_consent = graph_mod._require_cloud_llm_consent

    def consent_on_tty(svc, **kwargs):
        kwargs.setdefault("stdin_isatty", True)
        kwargs.setdefault("input_fn", fake_input)
        return real_consent(svc, **kwargs)

    monkeypatch.setattr(graph_mod, "_require_cloud_llm_consent", consent_on_tty)
    settings = ConnectSettings(
        ssh="user@host",
        remote_root="/opt/AgentCore",
        tenant="mir",
        workspace="dev",
        project="ThinkingSOC",
        source_server_path="/opt/ThinkingSOC",
    )
    args = Namespace(
        tenant=None,
        workspace=None,
        project=None,
        path=None,
        max_files=2000,
        allow_cloud_llm=False,
        cpu_percent="40",
        progress_interval=15.0,
        skip_nonconforming=True,
        sync_nonconforming=False,
        exclude_dir=["vendor"],
        include_path=["src/**"],
        include_ext=[".py"],
    )
    assert remote_sync_from_args(settings, args) == 0
    assert len(prompts) == 2
    assert "Allow cloud LLM" in prompts[0]
    cmd = seen[0]
    assert "--allow-cloud-llm" in cmd
    assert "--cpu-percent" in cmd and "40" in cmd
    assert "--progress-interval" in cmd and "15.0" in cmd
    assert "--skip-nonconforming" in cmd
    assert "--exclude-dir" in cmd and "vendor" in cmd
    assert "--include-path" in cmd and "src/**" in cmd
    assert "--include-ext" in cmd and ".py" in cmd
    from agentcore_cli.parser import build_parser

    parsed = build_parser().parse_args(cmd[1:])
    assert parsed.allow_cloud_llm is True
    assert parsed.skip_nonconforming is True
    assert parsed.cpu_percent == "40"


def test_remote_sync_forwards_allow_cloud_llm_without_reprompt(monkeypatch):
    seen: list[list[str]] = []
    monkeypatch.setattr(
        "agentcore_cli.connect_flow.remote_sync.run_ssh",
        lambda settings, remote_command, *, connect_timeout=15: seen.append(list(remote_command)) or 0,
    )
    monkeypatch.setattr("agentcore_cli.connect_flow.remote_sync.remote_is_dir", lambda *_a, **_k: True)
    monkeypatch.setattr(
        "agentcore_cli.connect_flow.remote_sync.remote_llm_config",
        lambda _settings: {
            "enabled": True,
            "api_base": "https://llm.example.com",
            "docs_enabled": True,
            "embeddings_enabled": False,
            "route_docs": {"primary_model": "openai/gpt-oss", "fallback_models": []},
            "route_embed": {"primary_model": "", "fallback_models": []},
        },
    )

    def boom(_prompt: str) -> str:
        raise AssertionError("must not prompt when --allow-cloud-llm already set")

    monkeypatch.setattr("agentcore_cli.commands.graph._read_cloud_llm_yes_no", boom)
    settings = ConnectSettings(
        ssh="user@host",
        remote_root="/opt/AgentCore",
        source_server_path="/opt/src",
    )
    args = Namespace(
        tenant="t",
        workspace="w",
        project="p",
        path=None,
        max_files=10,
        allow_cloud_llm=True,
        cpu_percent=None,
        progress_interval=30.0,
        skip_nonconforming=False,
        sync_nonconforming=False,
        exclude_dir=[],
        include_path=[],
        include_ext=[],
    )
    assert remote_sync_from_args(settings, args) == 0
    assert "--allow-cloud-llm" in seen[0]


def test_remote_sync_from_args_rejects_missing_server_path(monkeypatch):
    monkeypatch.setattr("agentcore_cli.connect_flow.remote_sync.remote_is_dir", lambda *_a, **_k: False)
    settings = ConnectSettings(
        ssh="user@host",
        remote_root="/opt/AgentCore",
        source_server_path="/opt/ThinkingSOC",
    )
    try:
        remote_sync_from_args(settings, Namespace(path=None, tenant=None, workspace=None, project=None))
        raised = False
    except SystemExit as exc:
        raised = True
        assert "not a directory on the AgentCore server" in str(exc)
        assert "/opt/ThinkingSOC" in str(exc)
    assert raised


def test_remote_ingest_skips_optional_when_path_missing_on_server(monkeypatch, capsys):
    calls: list[list[str]] = []

    def fake_run(settings, remote_command, *, connect_timeout=15):
        calls.append(list(remote_command))
        return 0

    monkeypatch.setattr("agentcore_cli.connect_flow.ingest.run_ssh", fake_run)
    monkeypatch.setattr("agentcore_cli.connect_flow.ingest.remote_is_dir", lambda *_a, **_k: False)
    settings = ConnectSettings(
        ssh="user@host",
        remote_root="/opt/AgentCore",
        tenant="mir",
        workspace="dev",
        project="ThinkingSOC",
        source_server_path="/opt/ThinkingSOC",
        ingest_mode="optional",
    )
    assert remote_ingest(settings) == 0
    assert calls == []
    out = capsys.readouterr().out
    assert "skipping ingest" in out
    assert "/opt/ThinkingSOC" in out


def test_remote_ingest_fails_always_when_path_missing_on_server(monkeypatch, capsys):
    monkeypatch.setattr("agentcore_cli.connect_flow.ingest.remote_is_dir", lambda *_a, **_k: False)
    settings = ConnectSettings(
        ssh="user@host",
        remote_root="/opt/AgentCore",
        source_server_path="/opt/missing",
        ingest_mode="always",
    )
    assert remote_ingest(settings) == 1
    err = capsys.readouterr().err
    assert "not a directory on the AgentCore server" in err


def test_cmd_sync_client_remote_helper(monkeypatch, tmp_path: Path):
    cfg = tmp_path / "connect.yaml"
    cfg.write_text(
        "server:\n  ssh: alice@srv\n  remote_root: /opt/AgentCore\n"
        "scope:\n  project: demo\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "agentcore_cli.connect_config.try_resolve_config_path",
        lambda explicit="": cfg,
    )
    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)

    def fake_remote(settings, args):
        assert settings.ssh == "alice@srv"
        assert args.force is True
        return 0

    monkeypatch.setattr(
        "agentcore_cli.connect_flow.remote_sync_from_args",
        fake_remote,
    )
    args = SimpleNamespace(force=True, path=None, tenant=None, workspace=None, project=None)
    assert sync_cmd._cmd_sync_client_remote(args) == 0


def test_cmd_sync_client_remote_without_connect_exits(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        "agentcore_cli.connect_config.try_resolve_config_path",
        lambda explicit="": None,
    )
    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)
    try:
        sync_cmd._cmd_sync_client_remote(SimpleNamespace())
        raised = False
    except SystemExit as exc:
        raised = True
        assert "Client installs" in str(exc)
    assert raised


def test_cmd_sync_routes_remote_when_role_client_even_with_compose(
    monkeypatch, tmp_path: Path
):
    compose = tmp_path / "backend" / "deployments" / "compose"
    compose.mkdir(parents=True, exist_ok=True)
    (compose / "compose.yaml").write_text("name: x\n", encoding="utf-8")
    (compose / ".env.local").write_text("A=1\n", encoding="utf-8")
    state = tmp_path / ".agentcore"
    state.mkdir(parents=True, exist_ok=True)
    (state / "install-state.env").write_text("role=client\n", encoding="utf-8")

    monkeypatch.setattr("agentcore_cli.commands.sync.cmd.repo_root", lambda: tmp_path)
    called: list[bool] = []

    def fake_remote(args):
        called.append(True)
        return 0

    def boom_start(_root):
        raise AssertionError("must not offer local start on client")

    monkeypatch.setattr(
        "agentcore_cli.commands.sync.cmd.cmd_sync_client_remote",
        fake_remote,
    )
    monkeypatch.setattr(
        "agentcore_cli.service_runtime.ensure_running_or_offer_start",
        boom_start,
    )
    args = SimpleNamespace(
        force=True,
        path=None,
        tenant=None,
        workspace=None,
        project=None,
        cpu_percent=None,
        allow_cloud_llm=False,
    )
    assert sync_cmd.cmd_sync(args) == 0
    assert called == [True]
