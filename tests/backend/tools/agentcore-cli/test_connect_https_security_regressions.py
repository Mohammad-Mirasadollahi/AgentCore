"""Security regression tests for API-only HTTPS connect (Task 8)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentcore_cli.connect_config import load_connect_settings


def _write_cfg(tmp_path: Path, body: str) -> Path:
    cfg_dir = tmp_path / ".agentcore"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg = cfg_dir / "connect.yaml"
    cfg.write_text(body, encoding="utf-8")
    return cfg


def test_https_scheme_fail_closed_without_override(tmp_path, monkeypatch):
    """Regression: HTTP URLs are rejected unless AGENTCORE_ALLOW_INSECURE_HTTP is set."""
    monkeypatch.delenv("AGENTCORE_ALLOW_INSECURE_HTTP", raising=False)
    cfg = _write_cfg(
        tmp_path,
        "server:\n  url: http://agentcore.example.internal:9\n"
        "scope:\n  tenant: t\n  workspace: w\n  project: p\n",
    )
    with pytest.raises(SystemExit, match="insecure"):
        load_connect_settings(config_path=str(cfg), allow_incomplete=True)


def test_connect_schema_rejects_ssh_only(tmp_path: Path):
    """Regression: server.ssh with no HTTPS alternative fails closed (Task 7)."""
    cfg = tmp_path / "connect.yaml"
    cfg.write_text(
        "server:\n  ssh: ops@host\n"
        "scope:\n  tenant: t\n  workspace: w\n  project: p\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="SSH has been removed"):
        load_connect_settings(config_path=str(cfg), allow_incomplete=True)


def test_https_wizard_does_not_write_agentcore_ssh_dir(tmp_path: Path, monkeypatch):
    """HTTPS wizard must not create legacy .agentcore/ssh material."""
    from agentcore_cli.connect_config import ConnectSettings
    from agentcore_cli.connect_wizard import run_https_connect_wizard

    monkeypatch.setattr("agentcore_cli.connect_wizard._require_tty", lambda: None)
    answers = iter(["https://agentcore.example:9443", "acme", "eng"])

    app = tmp_path / "MyApp"
    app.mkdir()
    cfg_path = tmp_path / ".agentcore" / "connect.yaml"
    run_https_connect_wizard(
        existing=ConnectSettings(project="MyApp", usage_profile="programming-cursor-mcp"),
        config_path=cfg_path,
        project_dir=app,
        input_fn=lambda _p: next(answers),
        password_fn=lambda _p: "",
    )
    agentcore_dir = tmp_path / ".agentcore"
    assert not (agentcore_dir / "ssh").exists()
    assert not list(agentcore_dir.glob("**/ssh*"))
