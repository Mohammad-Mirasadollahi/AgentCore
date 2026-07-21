"""Tests for HTTP MCP fragment materialization."""

from agentcore_cli.mcp_client_targets import materialize_http_mcp_fragment


def test_materialize_http_mcp_fragment():
    frag = materialize_http_mcp_fragment(
        url="http://agentcore.example.internal:32500/mcp",
        headers={"Authorization": "Bearer t", "X-Tenant-Id": "a"},
    )
    server = frag["mcpServers"]["AgentCore-Programming"]
    assert server["url"].endswith("/mcp")
    assert "command" not in server
    assert server["headers"]["Authorization"].startswith("Bearer ")
