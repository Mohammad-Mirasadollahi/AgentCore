from pathlib import Path

from usage_profile import (
    UsageProfileError,
    list_profile_ids,
    load_usage_profile,
    materialize_cursor_mcp_config,
    resolve_effective_profile,
    validate_usage_profile,
)


def test_catalog_includes_programming_profile():
    ids = list_profile_ids()
    assert "default" in ids
    assert "programming-cursor-mcp" in ids


def test_programming_profile_validates_and_lists_mcp_tools():
    profile = load_usage_profile("programming-cursor-mcp")
    assert profile["audience"] == "software-engineering"
    assert any(c["type"] == "ide_mcp" for c in profile["connectors"])
    names = {t["name"] for t in profile["mcp"]["tools"]}
    assert "agentcore_memory_retrieve" in names
    assert "agentcore_code_graph_search" in names
    assert "agentcore_code_graph_get_symbol" in names
    assert "agentcore_code_graph_neighbors" in names
    assert "agentcore_code_graph_impact" in names
    assert "agentcore_code_graph_generation_context" in names
    assert "agentcore_code_graph_ingest_file" in names
    assert "agentcore_code_graph_ingest_repo" in names
    assert "agentcore_guidance_resolve" in names
    assert "agentcore_guidance_get_skill" in names
    assert validate_usage_profile(profile) == []
    # Explore-first: PRIMARY code-graph tool appears before other graph tools.
    tool_names = [t["name"] for t in profile["mcp"]["tools"]]
    explore_i = tool_names.index("agentcore_code_graph_explore")
    assert explore_i == 2  # after ping + effective profile
    assert explore_i < tool_names.index("agentcore_code_graph_search")
    assert explore_i < tool_names.index("agentcore_memory_retrieve")


def test_resolve_and_materialize_cursor_mcp():
    effective = resolve_effective_profile(
        "programming-cursor-mcp",
        tenant_id="t1",
        workspace_id="w1",
        project_id="p1",
    )
    fragment = materialize_cursor_mcp_config(effective)
    server = fragment["mcpServers"]["agentcore-programming"]
    assert server["args"] == ["-m", "mcp_gateway_service"]
    assert server["env"]["AGENTCORE_USAGE_PROFILE"] == "programming-cursor-mcp"
    assert server["env"]["AGENTCORE_PROJECT_ID"] == "p1"


def test_invalid_profile_rejected(tmp_path: Path):
    bad = {"profile_id": "bad", "version": "1"}
    path = tmp_path / "bad.json"
    path.write_text('{"profile_id":"bad","version":"1"}', encoding="utf-8")
    errors = validate_usage_profile(bad)
    assert errors
    try:
        load_usage_profile("missing-profile-xyz")
        assert False, "expected error"
    except UsageProfileError:
        pass
