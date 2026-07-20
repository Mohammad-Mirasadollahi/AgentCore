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


def test_resolve_graph_mode_neo4j_when_password(monkeypatch):
    from mcp_gateway_service.store_factory import resolve_graph_mode

    env = {
        "AGENTCORE_MCP_STORE_MODE": "memory",
        "AGENTCORE_CODE_GRAPH_STORE": "neo4j",
        "AGENTCORE_NEO4J_PASSWORD": "secret",
    }
    assert resolve_graph_mode(env) == "neo4j"
    env["AGENTCORE_NEO4J_PASSWORD"] = "replace-with-a-local-secret"
    assert resolve_graph_mode(env) == "memory"
    env["AGENTCORE_MCP_GRAPH_MODE"] = "memory"
    env["AGENTCORE_NEO4J_PASSWORD"] = "secret"
    assert resolve_graph_mode(env) == "memory"


def test_code_graph_tools_neighbors_and_ingest():
    from uuid import uuid4

    from mcp_gateway_service.backends import PlatformBackends, dispatch_capability
    from mcp_gateway_service.store_factory import build_stores

    backends = PlatformBackends(build_stores({"AGENTCORE_MCP_STORE_MODE": "memory", "AGENTCORE_MCP_GRAPH_MODE": "memory"}))
    scope = {"tenant_id": "t", "workspace_id": "w", "project_id": "p"}
    ingested = dispatch_capability(
        backends,
        "code_graph.ingest_file",
        {
            "file_path": "src/util.py",
            "language": "python",
            "source": "def helper():\n    return 1\n\ndef caller():\n    return helper()\n",
        },
        scope=scope,
        usage_profile="programming-cursor-mcp",
        correlation_id=str(uuid4()),
    )
    assert ingested["graph_mode"] == "memory"
    assert ingested["ingest"]["symbols_indexed"] >= 2

    found = dispatch_capability(
        backends,
        "code_graph.get_symbol",
        {"qualified_name": "helper"},
        scope=scope,
        usage_profile="programming-cursor-mcp",
        correlation_id=str(uuid4()),
    )
    # qualified_name may be module-qualified depending on parser
    symbol = found["symbol"]
    assert "helper" in symbol["name"] or "helper" in symbol["qualified_name"]

    neighbors = dispatch_capability(
        backends,
        "code_graph.neighbors",
        {"symbol_id": symbol["id"], "max_depth": 1},
        scope=scope,
        usage_profile="programming-cursor-mcp",
        correlation_id=str(uuid4()),
    )
    assert "edges" in neighbors

    impact = dispatch_capability(
        backends,
        "code_graph.impact",
        {"symbol_id": symbol["id"], "max_depth": 2},
        scope=scope,
        usage_profile="programming-cursor-mcp",
        correlation_id=str(uuid4()),
    )
    assert impact["impact_of"] == symbol["id"]

    ctx = dispatch_capability(
        backends,
        "code_graph.generation_context",
        {"symbol_id": symbol["id"]},
        scope=scope,
        usage_profile="programming-cursor-mcp",
        correlation_id=str(uuid4()),
    )
    assert "seed" in ctx or "symbols" in ctx or "seed_symbol" in ctx or ctx.get("symbol") or "expansion" in ctx

    profile = dispatch_capability(
        backends,
        "code_graph.language_profile",
        {},
        scope=scope,
        usage_profile="programming-cursor-mcp",
        correlation_id=str(uuid4()),
    )
    assert "language_profile" in profile
    backends.close()


def test_code_graph_ingest_repo_via_mcp(tmp_path):
    from uuid import uuid4

    from mcp_gateway_service.backends import PlatformBackends, dispatch_capability
    from mcp_gateway_service.store_factory import build_stores

    (tmp_path / "mod.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    backends = PlatformBackends(
        build_stores({"AGENTCORE_MCP_STORE_MODE": "memory", "AGENTCORE_MCP_GRAPH_MODE": "memory"})
    )
    scope = {"tenant_id": "t", "workspace_id": "w", "project_id": "p-repo"}
    result = dispatch_capability(
        backends,
        "code_graph.ingest_repo",
        {"root_path": str(tmp_path), "include_outcomes": True},
        scope=scope,
        usage_profile="programming-cursor-mcp",
        correlation_id=str(uuid4()),
    )
    assert result["ingest_repo"]["files_ingested"] == 1
    assert result["ingest_repo"]["files_failed"] == 0
    got = dispatch_capability(
        backends,
        "code_graph.get_symbol",
        {"qualified_name": "hello"},
        scope=scope,
        usage_profile="programming-cursor-mcp",
        correlation_id=str(uuid4()),
    )
    assert "hello" in got["symbol"]["name"]
    backends.close()


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
