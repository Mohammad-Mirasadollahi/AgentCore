"""Tests for connect HTTP CA trust + bootstrap secret env + token/CA persist."""

from __future__ import annotations

from pathlib import Path

from agentcore_cli.connect_config import ConnectSettings, load_connect_settings
from agentcore_cli.connect_http import (
    httpx_verify,
    persist_access_token,
    persist_ca_pem,
    read_access_token_file,
)


def _write_cfg(tmp_path: Path, body: str) -> Path:
    cfg_dir = tmp_path / ".agentcore"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg = cfg_dir / "connect.yaml"
    cfg.write_text(body, encoding="utf-8")
    return cfg


def test_bootstrap_secret_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTCORE_CONNECT_BOOTSTRAP_SECRET", "op-secret-from-env")
    cfg = _write_cfg(
        tmp_path,
        "server:\n  url: https://agentcore.example.internal:9\n"
        "scope:\n  tenant: t\n  workspace: w\n  project: p\n",
    )
    settings = load_connect_settings(config_path=str(cfg), allow_incomplete=True)
    assert settings.bootstrap_secret == "op-secret-from-env"


def test_httpx_verify_uses_ca_file(tmp_path):
    ca = tmp_path / "ca.pem"
    ca.write_text("-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----\n")
    settings = ConnectSettings(ca_file=str(ca))
    assert httpx_verify(settings) == str(ca)


def test_httpx_verify_falls_back_to_system_trust(tmp_path, monkeypatch):
    monkeypatch.delenv("AGENTCORE_CONNECT_CA_FILE", raising=False)
    settings = ConnectSettings(ca_file=str(tmp_path / "missing.pem"))
    assert httpx_verify(settings) is True


def test_persist_and_reload_access_token(tmp_path):
    cfg = _write_cfg(
        tmp_path,
        "server:\n  url: https://agentcore.example.internal:9\n"
        "scope:\n  tenant: t\n  workspace: w\n  project: p\n",
    )
    path = persist_access_token(cfg, "ac1.example.token")
    assert path is not None
    assert path.stat().st_mode & 0o777 == 0o600
    assert read_access_token_file(cfg) == "ac1.example.token"
    settings = load_connect_settings(config_path=str(cfg), allow_incomplete=True)
    assert settings.api_token == "ac1.example.token"


def test_persist_ca_pem_auto_loaded(tmp_path, monkeypatch):
    monkeypatch.delenv("AGENTCORE_CONNECT_CA_FILE", raising=False)
    cfg = _write_cfg(
        tmp_path,
        "server:\n  url: https://agentcore.example.internal:9\n"
        "scope:\n  tenant: t\n  workspace: w\n  project: p\n",
    )
    pem = "-----BEGIN CERTIFICATE-----\nABC\n-----END CERTIFICATE-----\n"
    ca_path = persist_ca_pem(cfg, pem)
    assert ca_path is not None and ca_path.is_file()
    settings = load_connect_settings(config_path=str(cfg), allow_incomplete=True)
    assert settings.ca_file == str(ca_path)
    assert httpx_verify(settings) == str(ca_path)
