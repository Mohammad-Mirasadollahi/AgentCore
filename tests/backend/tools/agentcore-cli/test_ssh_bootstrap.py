"""Unit tests for AgentCore SSH identity bootstrap."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentcore_cli import ssh_bootstrap as sb


def test_ensure_identity_creates_ed25519(tmp_path: Path, monkeypatch):
    identity = tmp_path / "id_ed25519_agentcore"
    monkeypatch.setattr(sb, "default_identity_path", lambda: identity)
    result = sb.ensure_identity(identity=identity)
    assert result.private_path.is_file()
    assert result.public_path.is_file()
    assert result.old_public_line == ""
    assert sb.read_public_line(identity).startswith("ssh-ed25519 ")


def test_ensure_identity_rotate_replaces_key(tmp_path: Path):
    identity = tmp_path / "id_ed25519_agentcore"
    first = sb.ensure_identity(identity=identity)
    old_pub = first.public_path.read_text(encoding="utf-8")
    second = sb.ensure_identity(rotate=True, identity=identity)
    new_pub = second.public_path.read_text(encoding="utf-8")
    assert second.old_public_line == old_pub.strip().splitlines()[0].strip()
    assert new_pub != old_pub


def test_probe_batch_mode_false_on_missing_identity(tmp_path: Path):
    missing = tmp_path / "no-such-key"
    assert sb.probe_batch_mode("nobody@127.0.0.1", missing) is False


def test_install_pubkey_rejects_empty_password(tmp_path: Path):
    identity = tmp_path / "id_ed25519_agentcore"
    sb.ensure_identity(identity=identity)
    with pytest.raises(SystemExit, match="empty SSH password"):
        sb.install_pubkey("u@h", identity, "")


def test_install_pubkey_uses_askpass_and_wipes(tmp_path: Path, monkeypatch):
    identity = tmp_path / "id_ed25519_agentcore"
    sb.ensure_identity(identity=identity)
    seen: dict[str, object] = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        seen["env"] = kwargs.get("env") or {}
        askpass = Path(seen["env"]["SSH_ASKPASS"])
        seen["askpass_exists_during_run"] = askpass.is_file()
        seen["askpass_body"] = askpass.read_text(encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(sb.subprocess, "run", fake_run)
    sb.install_pubkey("ops@host", identity, "s3cret")
    assert seen["askpass_exists_during_run"] is True
    assert "s3cret" in str(seen["askpass_body"])
    assert seen["env"]["SSH_ASKPASS_REQUIRE"] == "force"
    assert "PreferredAuthentications=password" in seen["argv"]
    askpass_path = Path(seen["env"]["SSH_ASKPASS"])
    assert not askpass_path.exists()


def test_bootstrap_ssh_auth_rotate_cleans_old(tmp_path: Path, monkeypatch):
    identity = tmp_path / "id_ed25519_agentcore"
    calls: list[str] = []

    def fake_install(ssh_target, ident, password, **kwargs):
        calls.append(f"install:{ssh_target}")

    def fake_remove(ssh_target, ident, old_public_line, **kwargs):
        calls.append(f"remove:{old_public_line[:20]}")
        return True

    monkeypatch.setattr(sb, "install_pubkey", fake_install)
    monkeypatch.setattr(sb, "remove_old_pubkey", fake_remove)
    monkeypatch.setattr(sb, "probe_batch_mode", lambda *a, **k: True)

    sb.ensure_identity(identity=identity)
    result = sb.bootstrap_ssh_auth("ops@host", "pw", rotate=True, identity=identity)
    assert result.private_path == identity
    assert any(c.startswith("install:") for c in calls)
    assert any(c.startswith("remove:") for c in calls)
