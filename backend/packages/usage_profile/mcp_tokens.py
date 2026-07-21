"""Scoped bearer tokens for AgentCore MCP HTTP (shared by gateway + bootstrap)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


def extract_bearer(authorization: str | None) -> str:
    if not authorization:
        return ""
    parts = authorization.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return ""
    return parts[1].strip()


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def token_secret() -> str:
    return (
        os.environ.get("AGENTCORE_MCP_TOKEN_SECRET", "").strip()
        or os.environ.get("AGENTCORE_MCP_HTTP_TOKEN", "").strip()
    )


def mint_connect_token(
    *,
    tenant_id: str,
    workspace_id: str,
    project_id: str,
    ttl_seconds: int = 86400 * 30,
    secret: str | None = None,
) -> str:
    """Issue a scoped HMAC token (ac1.<payload>.<sig>)."""
    key = (secret if secret is not None else token_secret()).encode("utf-8")
    if not key:
        raise ValueError("AGENTCORE_MCP_TOKEN_SECRET or AGENTCORE_MCP_HTTP_TOKEN is required to mint tokens")
    payload = {
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "project_id": project_id,
        "exp": int(time.time()) + int(ttl_seconds),
    }
    body = _b64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    sig = _b64url_encode(hmac.new(key, body.encode("ascii"), hashlib.sha256).digest())
    return f"ac1.{body}.{sig}"


def verify_connect_token(
    token: str,
    *,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    project_id: str | None = None,
    secret: str | None = None,
    now: int | None = None,
) -> dict[str, str]:
    token = token.strip()
    static = (secret if secret is not None else os.environ.get("AGENTCORE_MCP_HTTP_TOKEN", "")).strip()
    hmac_secret = (secret if secret is not None else token_secret()).strip()

    if token.startswith("ac1."):
        if not hmac_secret:
            raise ValueError("server token secret not configured")
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("malformed token")
        _, body, sig = parts
        expected = _b64url_encode(
            hmac.new(hmac_secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected):
            raise ValueError("invalid token signature")
        try:
            payload: dict[str, Any] = json.loads(_b64url_decode(body).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("malformed token payload") from exc
        exp = int(payload.get("exp") or 0)
        if exp and int(now if now is not None else time.time()) > exp:
            raise ValueError("token expired")
        claim_t = str(payload.get("tenant_id") or "").strip()
        claim_w = str(payload.get("workspace_id") or "").strip()
        claim_p = str(payload.get("project_id") or "").strip()
        if not all((claim_t, claim_w, claim_p)):
            raise ValueError("token missing scope claims")
        if tenant_id and tenant_id != claim_t:
            raise ValueError("tenant header does not match token")
        if workspace_id and workspace_id != claim_w:
            raise ValueError("workspace header does not match token")
        if project_id and project_id != claim_p:
            raise ValueError("project header does not match token")
        return {"tenant_id": claim_t, "workspace_id": claim_w, "project_id": claim_p}

    if static and hmac.compare_digest(token, static):
        t = (tenant_id or "").strip()
        w = (workspace_id or "").strip()
        p = (project_id or "").strip()
        if not all((t, w, p)):
            raise ValueError("X-Tenant-Id, X-Workspace-Id, and X-Project-Id are required with shared token")
        return {"tenant_id": t, "workspace_id": w, "project_id": p}

    raise ValueError("unauthorized")
