"""Shared HTTPS client helpers for connect / content-push (CA trust + verify)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentcore_cli.connect_config import ConnectSettings

ACCESS_TOKEN_FILENAME = "access_token"
CA_PEM_REL = Path("certs") / "ca.pem"


def httpx_verify(settings: "ConnectSettings") -> str | bool:
    """Return httpx ``verify`` value: CA PEM path, or True (system trust)."""
    ca = str(getattr(settings, "ca_file", "") or "").strip()
    if ca and Path(ca).is_file():
        return ca
    env_ca = os.environ.get("AGENTCORE_CONNECT_CA_FILE", "").strip()
    if env_ca and Path(env_ca).is_file():
        return env_ca
    return True


def access_token_path(config_path: Path | None) -> Path | None:
    if config_path is None:
        return None
    return config_path.parent / ACCESS_TOKEN_FILENAME


def default_ca_path(config_path: Path | None) -> Path | None:
    if config_path is None:
        return None
    return config_path.parent / CA_PEM_REL


def read_access_token_file(config_path: Path | None) -> str:
    path = access_token_path(config_path)
    if path is None or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def persist_access_token(config_path: Path | None, token: str) -> Path | None:
    """Write minted access token next to connect.yaml (mode 0600). Never log token."""
    path = access_token_path(config_path)
    if path is None or not token.strip():
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        tmp.write_text(token.strip() + "\n", encoding="utf-8")
        os.chmod(tmp, 0o600)
        tmp.replace(path)
        os.chmod(path, 0o600)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
    return path


def persist_ca_pem(config_path: Path | None, ca_pem: str) -> Path | None:
    """Write bootstrap ``ca_pem`` under ``.agentcore/certs/ca.pem``."""
    path = default_ca_path(config_path)
    text = (ca_pem or "").strip()
    if path is None or not text:
        return None
    if "BEGIN CERTIFICATE" not in text:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.chmod(tmp, 0o644)
        tmp.replace(path)
        os.chmod(path, 0o644)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
    return path
