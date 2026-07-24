"""Platform seed pack: MCP-first always-on rule, agents entry, and capability skills.

Prompt bodies live in ``seed_mcp_first_prompts/`` — one Markdown file per item.
They are loaded separately and never concatenated into a single blob.

Documentation-authoring skill body remains in ``documentation_authoring_law``
(its own module; not merged into this pack's prompt files).
"""

from __future__ import annotations

from typing import Any

from common_context_service.documentation_authoring_law import (
    SKILL_MARKDOWN as DOCUMENTATION_AUTHORING_SKILL_BODY,
)
from common_context_service.seed_mcp_first_prompts import load_prompt

# Normative bodies aligned with docs/15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md

SEED_PACK_ID = "awg-seed-mcp-first-programming"
# Bump when rule/skill/entry bodies change so client store + disk refresh.
SEED_PACK_VERSION = "2026.07.24.5"

MCP_FIRST_RULE_BODY = load_prompt("always_rule_mcp_first.md")
AGENTS_ENTRY_BODY = load_prompt("agents_entry.md")

# Metadata only — each skill body is a dedicated file under prompts/skills/
# (except documentation-authoring, owned by documentation_authoring_law).
_SKILL_SPECS: list[dict[str, Any]] = [
    {
        "name": "agentcore-session-bootstrap",
        "description": "Bootstrap an AgentCore MCP session—ping, profile, resolve guidance, then code.",
        "when_to_use": ["session-start", "mcp", "bootstrap"],
        "title": "AgentCore session bootstrap",
        "prompt_file": "agentcore-session-bootstrap.md",
    },
    {
        "name": "agentcore-memory",
        "description": "Retrieve or persist project memory through AgentCore MCP.",
        "when_to_use": ["memory", "recall", "remember"],
        "title": "AgentCore memory",
        "prompt_file": "agentcore-memory.md",
    },
    {
        "name": "agentcore-code-graph",
        "description": "Search AgentCore code knowledge graph before wide local search.",
        "when_to_use": ["code-graph", "symbols", "search"],
        "title": "AgentCore code graph",
        "prompt_file": "agentcore-code-graph.md",
    },
    {
        "name": "agentcore-remove-dead-code",
        "description": "Prove and delete orphaned symbols, imports, and exclusive tests after a replace or retire.",
        "when_to_use": ["dead-code", "unused", "cleanup", "orphan"],
        "title": "AgentCore remove dead code",
        "prompt_file": "agentcore-remove-dead-code.md",
    },
    {
        "name": "agentcore-durable-write",
        "description": "Write memory, task, activity, or decision records via AgentCore MCP.",
        "when_to_use": ["write", "persist", "decision", "activity"],
        "title": "AgentCore durable write",
        "prompt_file": "agentcore-durable-write.md",
    },
    {
        "name": "agentcore-documentation-authoring",
        "description": (
            "Full-tier ThinkingSOC/AgentCore Markdown authoring law — call before writing, "
            "explaining, or fix-on-read remediating product documentation."
        ),
        "when_to_use": [
            "documentation",
            "docs",
            "authoring",
            "standards",
            "frontmatter",
            "how-to-write-docs",
            "remediate",
            "fix-on-read",
        ],
        "title": "AgentCore documentation authoring",
        "prompt_file": None,
        "body": DOCUMENTATION_AUTHORING_SKILL_BODY,
    },
    {
        "name": "agentcore-docs-sync",
        "description": (
            "Run AgentCore docs-sync drift, status, Body-tier validate, note, draft, and index via MCP. "
            "For Full-tier product docs, load agentcore-documentation-authoring first."
        ),
        "when_to_use": ["docs-sync", "drift", "coverage", "docs-index"],
        "title": "AgentCore docs sync",
        "prompt_file": "agentcore-docs-sync.md",
    },
    {
        "name": "agentcore-source-contracts",
        "description": (
            "Selective hard-module contract docstrings (standard 49) and package/folder "
            "README maps (standard 50) — apply on edit and fix-on-read of hard modules."
        ),
        "when_to_use": [
            "module-contract",
            "docstring",
            "package-readme",
            "folder-readme",
            "source-of-truth",
            "fail-open",
            "hard-module",
            "fix-on-read",
        ],
        "title": "AgentCore source contracts (49/50)",
        "prompt_file": "agentcore-source-contracts.md",
    },
    {
        "name": "agentcore-standards-on-edit",
        "description": (
            "Fix-on-write: whenever you create or edit product docs or hard-module code, "
            "remediate to project standards in the same turn so the corpus converges."
        ),
        "when_to_use": [
            "fix-on-write",
            "standards",
            "remediate",
            "edit",
            "nonconforming",
            "sync-skip",
        ],
        "title": "AgentCore standards on edit",
        "prompt_file": "agentcore-standards-on-edit.md",
    },
    {
        "name": "agentcore-quality-audit",
        "description": (
            "Run agentcore_quality_audit; remediate high/medium docs+code findings "
            "or create durable tasks before treating work as done."
        ),
        "when_to_use": [
            "quality-audit",
            "quality",
            "debt",
            "nonconforming",
            "stale",
            "session-start",
            "remediate",
        ],
        "title": "AgentCore quality audit",
        "prompt_file": "agentcore-quality-audit.md",
    },
    {
        "name": "agentcore-create-task",
        "description": "Create a durable AgentCore Task for follow-up engineering work.",
        "when_to_use": ["task", "follow-up", "track"],
        "title": "AgentCore create task",
        "prompt_file": "agentcore-create-task.md",
    },
]


def _skill_body(spec: dict[str, Any]) -> str:
    prompt_file = spec.get("prompt_file")
    if prompt_file:
        return load_prompt("skills", str(prompt_file))
    body = spec.get("body")
    if isinstance(body, str) and body.strip():
        return body if body.endswith("\n") else body + "\n"
    raise ValueError(f"skill {spec.get('name')!r} has neither prompt_file nor body")


def _skills() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for spec in _SKILL_SPECS:
        out.append(
            {
                "name": spec["name"],
                "description": spec["description"],
                "when_to_use": list(spec["when_to_use"]),
                "title": spec["title"],
                "body": _skill_body(spec),
            }
        )
    return out


def mcp_first_seed_payloads() -> list[dict[str, Any]]:
    """Return propose payloads for the awg-seed-mcp-first-programming pack."""
    payloads: list[dict[str, Any]] = [
        {
            "item_type": "agents_entry",
            "title": "Agent entry",
            "body": AGENTS_ENTRY_BODY,
            "confidence": 1.0,
            "user_pinning": 1.0,
            "workflow_type": "coding",
            "seed_pack": SEED_PACK_ID,
            "seed_pack_version": SEED_PACK_VERSION,
        },
        {
            "item_type": "always_rule",
            "slug": "mcp-first-agentcore",
            "title": "MCP-first AgentCore",
            "body": MCP_FIRST_RULE_BODY,
            "priority": 1000,
            "mandatory": True,
            "confidence": 1.0,
            "user_pinning": 1.0,
            "workflow_type": "coding",
            "seed_pack": SEED_PACK_ID,
            "seed_pack_version": SEED_PACK_VERSION,
        },
    ]
    for skill in _skills():
        payloads.append(
            {
                "item_type": "skill",
                "name": skill["name"],
                "description": skill["description"],
                "when_to_use": skill["when_to_use"],
                "title": skill["title"],
                "body": skill["body"],
                "confidence": 1.0,
                "user_pinning": 1.0,
                "workflow_type": "coding",
                "seed_pack": SEED_PACK_ID,
                "seed_pack_version": SEED_PACK_VERSION,
            }
        )
    return payloads


def mcp_first_seed_skill_names() -> set[str]:
    return {
        str(p.get("name") or "").strip()
        for p in mcp_first_seed_payloads()
        if p.get("item_type") == "skill" and str(p.get("name") or "").strip()
    }
