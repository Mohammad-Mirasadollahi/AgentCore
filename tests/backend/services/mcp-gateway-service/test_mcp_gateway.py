import json

from mcp_gateway_service.backends.platform import PlatformBackends
from mcp_gateway_service.server import McpGateway, McpGatewayError, handle_message
from mcp_gateway_service.store_factory import build_stores


def gateway():
    return McpGateway(
        profile_id="programming-cursor-mcp",
        tenant_id="t",
        workspace_id="w",
        project_id="p",
        backends=PlatformBackends(
            build_stores(
                {
                    "AGENTCORE_MCP_STORE_MODE": "memory",
                    "AGENTCORE_MCP_GRAPH_MODE": "memory",
                }
            )
        ),
    )


def test_tools_list_is_lazy_facade():
    gw = gateway()
    tools = gw.tools_list()
    names = {t["name"] for t in tools}
    assert names == {"mcp_search_tools", "mcp_execute_tool"}
    assert all("inputSchema" in t for t in tools)
    catalog = {t["name"] for t in gw.catalog_tools()}
    assert "agentcore_ping" in catalog
    assert "agentcore_guidance_resolve" in catalog
    assert "agentcore_create_task" in catalog
    assert "agentcore_docs_authoring_standards" in catalog
    assert "agentcore_docs_catalog" in catalog
    assert "agentcore_quality_audit" in catalog


def test_initialize_and_tools_list_rpc():
    gw = gateway()
    init = handle_message(
        gw,
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )
    assert init["result"]["serverInfo"]["name"] == "AgentCore-Programming"
    listed = handle_message(gw, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    assert {t["name"] for t in listed["result"]["tools"]} == {
        "mcp_search_tools",
        "mcp_execute_tool",
    }


def test_lazy_search_and_execute():
    gw = gateway()
    search = gw.call_tool("mcp_search_tools", {"query": "guidance resolve", "limit": 5})
    hits = search["structuredContent"]["results"]
    assert hits
    assert any(h["tool_name"] == "agentcore_guidance_resolve" for h in hits)
    assert all(h["server_name"] == "AgentCore-Programming" for h in hits)
    assert all("inputSchema" in h for h in hits)

    executed = gw.call_tool(
        "mcp_execute_tool",
        {
            "server_name": "AgentCore-Programming",
            "tool_name": "agentcore_ping",
            "arguments": {},
        },
    )
    assert executed["structuredContent"]["ok"] is True

    via_aliases = gw.call_tool(
        "mcp_execute_tool",
        {"server": "AgentCore-Programming", "tool": "agentcore_ping", "arguments": {}},
    )
    assert via_aliases["structuredContent"]["ok"] is True


def test_tools_call_wired_backends():
    gw = gateway()
    ping = handle_message(
        gw,
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "agentcore_ping", "arguments": {}},
        },
    )
    ping_payload = json.loads(ping["result"]["content"][0]["text"])
    assert ping_payload["ok"] is True
    assert ping_payload["backend"] == "in_process"

    memory = gw.call_tool("agentcore_memory_retrieve", {"query": "idempotency keys for APIs"})
    memory_payload = memory["structuredContent"]
    assert memory_payload["backend"] == "in_process"
    assert memory_payload["items"]

    graph = gw.call_tool("agentcore_code_graph_search", {"query": "hash_password", "top_k": 3})
    assert graph["structuredContent"]["symbols"]

    task = gw.call_tool("agentcore_create_task", {"title": "Wire MCP", "instructions": "done"})
    assert task["structuredContent"]["task"]["kind"] == "task"
    assert task["structuredContent"]["task"]["data"]["title"] == "Wire MCP"

    drift = gw.call_tool("agentcore_docs_drift_check", {"symbol": "auth.hash_password"})
    assert drift["structuredContent"]["drift"] is True
    assert drift["structuredContent"]["findings"]

    written = gw.call_tool(
        "agentcore_write",
        {
            "resource": "memory",
            "title": "Prefer scoped MCP writes",
            "body": "Cursor should persist conventions via agentcore_write into memory.",
            "tags": ["cursor", "convention"],
        },
    )
    assert written["structuredContent"]["written"] == "memory"
    assert written["structuredContent"]["memory"]["title"] == "Prefer scoped MCP writes"

    activity = gw.call_tool(
        "agentcore_write",
        {"resource": "activity", "summary": "Connected Cursor MCP and wrote a note"},
    )
    assert activity["structuredContent"]["written"] == "activity"

    docs_note = gw.call_tool(
        "agentcore_docs_write",
        {
            "mode": "note",
            "title": "Auth hashing notes",
            "body": "# Auth\n\nUse scoped APIs when hashing passwords.",
            "symbol": "auth.hash_password",
            "file_path": "src/auth/hash.py",
        },
    )
    assert docs_note["structuredContent"]["written"] == "document"
    assert docs_note["structuredContent"]["anchor"] is not None

    docs_draft = gw.call_tool(
        "agentcore_docs_write",
        {
            "mode": "draft",
            "title": "hash_password draft",
            "body": "Documents password hashing helper.",
            "symbol": "auth.hash_password",
        },
    )
    assert docs_draft["structuredContent"]["written"] == "draft"

    validated = gw.call_tool(
        "agentcore_docs_write",
        {
            "mode": "validate",
            "title": "Check FM",
            "symbol": "auth.hash_password",
        },
    )
    assert validated["structuredContent"]["ok"] is True

    status = gw.call_tool("agentcore_docs_status", {})
    assert "coverage" in status["structuredContent"]
    assert "missing_count" in status["structuredContent"]

    authoring = gw.call_tool("agentcore_docs_authoring_standards", {})
    standards = authoring["structuredContent"]["authoring_standards"]
    assert standards["law_id"] == "agentcore.documentation_authoring.full_tier"
    assert "doc_id" in standards["required_frontmatter_keys"]
    assert "agentcore-documentation-authoring" == standards["skill_name"]
    assert "agentcore_docs_catalog" in standards["related_mcp_tools"]
    assert "agentcore_quality_audit" in standards["related_mcp_tools"]

    catalog = gw.call_tool(
        "agentcore_docs_catalog",
        {"query": "hybrid", "limit": 5, "refresh": False},
    )
    cat = catalog["structuredContent"]
    assert cat["mode"] == "docs_catalog_query"
    assert cat["invents_edges"] is False
    assert cat.get("vocabulary_source") == "observed_frontmatter"
    assert "vocabularies" in cat
    assert "documents" in cat

    qa = gw.call_tool(
        "agentcore_quality_audit",
        {"top_n": 5, "severities": ["high", "medium"]},
    )
    qa_body = qa["structuredContent"]
    assert qa_body["maps_to"] == "quality.audit"
    assert "must_remediate" in qa_body
    assert "findings" in qa_body
    assert "agent_instruction" in qa_body

    guidance = gw.call_tool(
        "agentcore_guidance_resolve",
        {"task_summary": "start coding with AgentCore MCP"},
    )
    bundle = guidance["structuredContent"]["bundle"]
    assert bundle["agents_entry"] is not None
    assert any(r.get("slug") == "mcp-first-agentcore" for r in bundle["always_rules"])
    assert any(s["name"] == "agentcore-session-bootstrap" for s in bundle["skills"])

    listed = gw.call_tool("agentcore_guidance_list_skills", {"query": "docs"})
    skill_names = {s["name"] for s in listed["structuredContent"]["skills"]}
    assert "agentcore-docs-sync" in skill_names
    assert "agentcore-documentation-authoring" in skill_names

    skill = gw.call_tool(
        "agentcore_guidance_get_skill",
        {"name": "agentcore-code-graph", "bundle_id": bundle["bundle_id"]},
    )
    assert "agentcore_code_graph_search" in skill["structuredContent"]["skill"]["body"]

    authoring_skill = gw.call_tool(
        "agentcore_guidance_get_skill",
        {"name": "agentcore-documentation-authoring", "bundle_id": bundle["bundle_id"]},
    )
    assert "agentcore_docs_authoring_standards" in authoring_skill["structuredContent"]["skill"]["body"]
    assert "Full-tier" in authoring_skill["structuredContent"]["skill"]["body"]


def test_unknown_tool_fails_closed():
    gw = gateway()
    bad = handle_message(
        gw,
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "not_allowed_tool", "arguments": {}},
        },
    )
    assert bad["error"]["code"] == -32601


def test_write_requires_resource_fields():
    gw = gateway()
    try:
        gw.call_tool("agentcore_write", {"resource": "memory", "title": "missing body"})
        assert False, "expected error"
    except McpGatewayError as exc:
        assert "body" in exc.message


def test_create_task_requires_title():
    gw = gateway()
    try:
        gw.call_tool("agentcore_create_task", {})
        assert False, "expected error"
    except McpGatewayError as exc:
        assert "title" in exc.message
