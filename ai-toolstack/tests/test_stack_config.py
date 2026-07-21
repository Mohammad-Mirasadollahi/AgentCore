"""Ai-toolstack stack config (MCP: mcp-lazy only; backends memory + headroom)."""

from __future__ import annotations

import unittest
from pathlib import Path


class StackConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[2]
        cls.ai = root / "ai-toolstack"
        cls.rules = cls.ai / "rules"
        cls.servers_tpl = cls.ai / "config" / "mcp-lazy-servers.json.template"
        cls.mcp_tpl = cls.ai / "config" / "mcp.json.template"
        cls.vendor_skill = cls.ai / "skills" / "vendor" / "ponytail" / "ponytail" / "SKILL.md"

    def test_mcp_lazy_servers_template(self) -> None:
        text = self.servers_tpl.read_text(encoding="utf-8")
        self.assertIn('"memory"', text)
        self.assertIn('"headroom"', text)
        self.assertNotIn('"graphify"', text)
        self.assertNotIn('"code-review-graph"', text)
        self.assertNotIn('"graphify-read"', text)

    def test_mcp_json_template_single_cursor_entry(self) -> None:
        text = self.mcp_tpl.read_text(encoding="utf-8")
        self.assertIn('"mcp-lazy"', text)
        self.assertNotIn('"headroom"', text)
        self.assertNotIn('"memory"', text)
        self.assertNotIn('"graphify"', text)

    def test_removed_rules(self) -> None:
        for name in (
            "graphify.mdc",
            "code-review-graph.mdc",
            "caveman-stack-cursor.mdc",
            "ponytail-stack-cursor.mdc",
            "mcp-first-agent.mdc",
        ):
            self.assertFalse((self.rules / name).exists(), name)

    def test_graphify_enrichment_package_removed(self) -> None:
        self.assertFalse((self.ai / "lib" / "graphify_enrichment").exists())

    def test_ponytail_project_rule_present(self) -> None:
        self.assertTrue((self.rules / "ponytail.mdc").is_file())

    def test_sync_ponytail_does_not_overwrite_project_rule(self) -> None:
        script = (self.ai / "scripts" / "sync-ponytail-vendor.sh").read_text(encoding="utf-8")
        self.assertIn("Does NOT overwrite", script)
        self.assertIn("upstream-ponytail.mdc", script)
        self.assertNotIn(
            'cp "${TMP}/ponytail/.cursor/rules/ponytail.mdc" "${AI_TOOLSTACK_RULES}/ponytail.mdc"',
            script,
        )

    def test_auto_install_config_present(self) -> None:
        path = self.ai / "config" / "auto-install.env.sh"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("AI_TOOLSTACK_AUTO_INSTALL", text)
        self.assertIn("AI_TOOLSTACK_AUTO_INSTALL_RTK", text)

    def test_review_thinkingsoc_skill_present(self) -> None:
        skill = self.ai / "skills" / "thinkingsoc" / "review-thinkingSOC" / "SKILL.md"
        self.assertTrue(skill.is_file())
        self.assertIn("bugbot", skill.read_text(encoding="utf-8").lower())

    def test_removed_thinkingsoc_skills(self) -> None:
        think = self.ai / "skills" / "thinkingsoc"
        for name in ("ponytail-cursor-stack", "persian-chat-reply"):
            self.assertFalse((think / name).exists(), name)
        global_persian = (
            self.ai / "cursor-agent-config" / "global-skills" / "persian-chat-reply" / "SKILL.md"
        )
        self.assertTrue(global_persian.is_file())

    def test_agentcore_entrypoints_present(self) -> None:
        ep = self.ai / "cursor-agent-config" / "entrypoints"
        self.assertTrue((ep / "AGENTS.agentcore.md").is_file())
        self.assertTrue((ep / ".cursorrules.agentcore").is_file())

    def test_ponytail_vendor_skill(self) -> None:
        self.assertTrue(self.vendor_skill.is_file())


if __name__ == "__main__":
    unittest.main()
