"""Unit tests for Full-tier documentation authoring law payload."""

from __future__ import annotations

from common_context_service.documentation_authoring_law import (
    REQUIRED_FRONTMATTER_KEYS,
    SKILL_MARKDOWN,
    authoring_law_payload,
)
from common_context_service.seed_mcp_first import mcp_first_seed_payloads


def test_authoring_law_payload_has_full_tier_checklist():
    payload = authoring_law_payload()
    assert payload["law_id"] == "agentcore.documentation_authoring.full_tier"
    assert "doc_id" in payload["required_frontmatter_keys"]
    assert set(REQUIRED_FRONTMATTER_KEYS).issubset(set(payload["required_frontmatter_keys"]))
    assert any("Mermaid" in item for item in payload["hard_requirements"])
    assert "agentcore docs-standards" in payload["cli_gates"]
    assert "Body-tier" in payload["tier_boundary"]["body_tier"]
    assert "Full-tier" in payload["tier_boundary"]["full_tier"]
    assert "NOT Full-tier" in payload["tier_boundary"]["body_tier"]


def test_seed_includes_documentation_authoring_skill():
    skills = [p for p in mcp_first_seed_payloads() if p.get("item_type") == "skill"]
    names = {p["name"] for p in skills}
    assert "agentcore-documentation-authoring" in names
    assert "agentcore-docs-sync" in names
    authoring = next(p for p in skills if p["name"] == "agentcore-documentation-authoring")
    assert authoring["body"] == SKILL_MARKDOWN
    assert "agentcore_docs_authoring_standards" in authoring["body"]
    docs_sync = next(p for p in skills if p["name"] == "agentcore-docs-sync")
    assert "Full-tier" in docs_sync["body"] or "agentcore_docs_authoring_standards" in docs_sync["body"]


def test_mcp_first_rule_requires_authoring_standards_tool():
    rule = next(p for p in mcp_first_seed_payloads() if p.get("item_type") == "always_rule")
    assert "agentcore_docs_authoring_standards" in rule["body"]
    assert "Full-tier" in rule["body"]
