from mcp_gateway_service.lazy_facade import search_catalog, server_name_aliases


def test_search_ranks_guidance_resolve():
    tools = [
        {
            "name": "agentcore_ping",
            "description": "Confirm MCP connectivity",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "agentcore_guidance_resolve",
            "description": "Resolve workspace guidance before coding",
            "input_schema": {"type": "object", "properties": {"task_summary": {"type": "string"}}},
        },
    ]
    out = search_catalog(tools, server_name="AgentCore-Programming", query="guidance resolve", limit=3)
    assert out["results"][0]["tool_name"] == "agentcore_guidance_resolve"
    assert out["results"][0]["server_name"] == "AgentCore-Programming"
    assert "inputSchema" in out["results"][0]


def test_search_empty_suggests_keywords():
    out = search_catalog([], server_name="AgentCore-Programming", query="zzz", limit=5)
    assert out["results"] == []
    assert "AgentCore-Programming" in out["suggestion"]


def test_server_aliases_include_canonical_casefold():
    aliases = server_name_aliases("AgentCore-Programming")
    assert "AgentCore-Programming" in aliases
    assert "agentcore-programming" in aliases  # lower() of canonical
