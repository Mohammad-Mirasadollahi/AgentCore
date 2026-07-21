"""Tests for MCP HTTP token auth and gateway."""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from usage_profile.mcp_tokens import mint_connect_token, verify_connect_token


def test_mint_and_verify_scoped_token(monkeypatch):
    monkeypatch.setenv("AGENTCORE_MCP_TOKEN_SECRET", "unit-test-secret-key-32chars!!")
    token = mint_connect_token(tenant_id="t", workspace_id="w", project_id="p", ttl_seconds=60)
    scope = verify_connect_token(token)
    assert scope == {"tenant_id": "t", "workspace_id": "w", "project_id": "p"}


def test_verify_rejects_wrong_project_header(monkeypatch):
    monkeypatch.setenv("AGENTCORE_MCP_TOKEN_SECRET", "unit-test-secret-key-32chars!!")
    token = mint_connect_token(tenant_id="t", workspace_id="w", project_id="p")
    with pytest.raises(ValueError, match="project"):
        verify_connect_token(token, project_id="other")


def test_static_token_requires_scope_headers(monkeypatch):
    monkeypatch.setenv("AGENTCORE_MCP_HTTP_TOKEN", "shared-lab-token-value")
    scope = verify_connect_token(
        "shared-lab-token-value",
        tenant_id="t",
        workspace_id="w",
        project_id="p",
        secret="shared-lab-token-value",
    )
    assert scope["project_id"] == "p"
    with pytest.raises(ValueError):
        verify_connect_token("shared-lab-token-value", secret="shared-lab-token-value")


def test_http_mcp_initialize(monkeypatch):
    monkeypatch.setenv("AGENTCORE_MCP_TOKEN_SECRET", "unit-test-secret-key-32chars!!")
    monkeypatch.setenv("AGENTCORE_MCP_STORE_MODE", "memory")
    from mcp_gateway_service.http_app import create_http_app

    token = mint_connect_token(tenant_id="t", workspace_id="w", project_id="p")
    app = create_http_app()

    async def run() -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            health = await client.get("/health")
            assert health.status_code == 200
            denied = await client.post(
                "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"}
            )
            assert denied.status_code == 401
            ok = await client.post(
                "/mcp",
                headers={"Authorization": f"Bearer {token}"},
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            )
            assert ok.status_code == 200
            assert "result" in ok.json()
            tools = await client.post(
                "/mcp",
                headers={"Authorization": f"Bearer {token}"},
                json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            )
            assert tools.status_code == 200
            listed = {t["name"] for t in tools.json()["result"]["tools"]}
            assert listed == {"mcp_search_tools", "mcp_execute_tool"}

    asyncio.run(run())
