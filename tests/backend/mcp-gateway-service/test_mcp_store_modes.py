from __future__ import annotations

from uuid import uuid4

from mcp_gateway_service.backends import PlatformBackends, dispatch_capability
from mcp_gateway_service.server import McpGateway, handle_message
from mcp_gateway_service.store_factory import build_stores, resolve_store_mode


def test_resolve_store_mode_defaults_to_memory(monkeypatch):
    monkeypatch.delenv("AGENTCORE_MCP_STORE_MODE", raising=False)
    monkeypatch.delenv("AGENTCORE_DATABASE_URL", raising=False)
    assert resolve_store_mode({}) == "memory"


def test_resolve_store_mode_postgres_when_url(monkeypatch):
    env = {"AGENTCORE_DATABASE_URL": "postgresql://agentcore:x@127.0.0.1:32232/agentcore"}
    assert resolve_store_mode(env) == "postgres"
    env["AGENTCORE_MCP_STORE_MODE"] = "memory"
    assert resolve_store_mode(env) == "memory"


def test_build_stores_memory_bundle():
    bundle = build_stores({"AGENTCORE_MCP_STORE_MODE": "memory"})
    assert bundle.mode == "memory"
    backends = PlatformBackends(bundle)
    assert backends.store_mode == "memory"
    ping = dispatch_capability(
        backends,
        "platform.ping",
        {},
        scope={"tenant_id": "t", "workspace_id": "w", "project_id": "p"},
        usage_profile="default",
        correlation_id=str(uuid4()),
    )
    assert ping["store_mode"] == "memory"
    backends.close()


def test_gateway_reports_store_mode():
    gw = McpGateway(
        profile_id="programming-cursor-mcp",
        tenant_id="t",
        workspace_id="w",
        project_id="p",
        backends=PlatformBackends(build_stores({"AGENTCORE_MCP_STORE_MODE": "memory"})),
    )
    result = handle_message(
        gw,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "agentcore_ping", "arguments": {}},
        },
    )
    import json

    payload = json.loads(result["result"]["content"][0]["text"])
    assert payload["store_mode"] == "memory"
    gw.backends.close()


def test_create_task_persists_in_memory_store():
    backends = PlatformBackends.from_env({"AGENTCORE_MCP_STORE_MODE": "memory"})
    scope = {"tenant_id": "t", "workspace_id": "w", "project_id": "p"}
    created = dispatch_capability(
        backends,
        "core_data.create_task",
        {"title": "Persist me", "instructions": "via MCP"},
        scope=scope,
        usage_profile="programming-cursor-mcp",
        correlation_id=str(uuid4()),
    )
    assert created["store_mode"] == "memory"
    assert created["task"]["data"]["title"] == "Persist me"
    backends.close()
