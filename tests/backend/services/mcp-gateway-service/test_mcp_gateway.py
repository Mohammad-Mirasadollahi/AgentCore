import json

from mcp_gateway_service.server import McpGateway, McpGatewayError, handle_message


def gateway():
    return McpGateway(
        profile_id="programming-cursor-mcp",
        tenant_id="t",
        workspace_id="w",
        project_id="p",
    )


def test_tools_list_matches_usage_profile():
    gw = gateway()
    tools = gw.tools_list()
    names = {t["name"] for t in tools}
    assert "agentcore_ping" in names
    assert "agentcore_create_task" in names
    assert "agentcore_write" in names
    assert "agentcore_docs_write" in names
    assert "agentcore_docs_status" in names
    assert all("inputSchema" in t for t in tools)


def test_initialize_and_tools_list_rpc():
    gw = gateway()
    init = handle_message(
        gw,
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )
    assert init["result"]["serverInfo"]["name"] == "agentcore-programming"
    listed = handle_message(gw, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    assert len(listed["result"]["tools"]) >= 4


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
