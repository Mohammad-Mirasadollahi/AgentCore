"""Platform seed pack: MCP-first always-on rule, agents entry, and capability skills."""

from __future__ import annotations

from typing import Any

from common_context_service.documentation_authoring_law import SKILL_MARKDOWN as DOCUMENTATION_AUTHORING_SKILL_BODY

# Normative bodies aligned with docs/15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md

MCP_FIRST_RULE_BODY = """# MCP-first AgentCore

When this workspace is connected to AgentCore over MCP (lazy facade: `mcp_search_tools` → `mcp_execute_tool`):

1. Search then execute `agentcore_guidance_resolve` before substantive coding.
2. For capabilities AgentCore exposes on the active Usage Profile, prefer the matching MCP tool over inventing a local-only substitute.
3. Do not store project facts only in chat when `agentcore_write` or `agentcore_memory_retrieve` can persist or recall them.
4. Do not skip code-graph search when locating symbols AgentCore can index.
5. Do not skip docs-sync tools when checking drift, coverage, or drafting docs AgentCore governs.
6. When implementing, replacing, or retiring behavior, remove orphaned predecessors in the **same change** after proof: unused imports, superseded symbols, exclusive tests, and stale re-exports. Prefer `agentcore_code_graph_unused_candidates` when listed; otherwise prove with graph explore + repository search. Skip anything marked live-until-proven (dynamic registries, public HTTP/IAM exports, `tsoc-defer`). AgentCore does not delete files — you do.
7. When the user asks how documentation works, or when writing/remediating product Markdown under `docs/` (or other normative doc trees): call `agentcore_docs_authoring_standards` and follow skill `agentcore-documentation-authoring`. Docs-sync `validate` is Body-tier only — not Full-tier compliance.
8. If a needed capability is missing from `mcp_search_tools` results, execute `agentcore_get_effective_profile`, report the gap, and ask before bypassing with unmanaged workflows.
9. Keep identifiers, paths, and committed docs in English; follow any other always-on project rules from the guidance bundle.
"""

AGENTS_ENTRY_BODY = """# Agent entry

**Law:** MCP-first AgentCore (always-on rule `mcp-first-agentcore`).

## Session start

1. Resolve workspace guidance via MCP when tools are available.
2. Follow always-on rules from the bundle.
3. Open the matching skill before large memory, graph, docs, or durable-write work.

## High-signal skills

| Skill | Use when |
| --- | --- |
| `agentcore-session-bootstrap` | Starting a coding session on an AgentCore-connected project |
| `agentcore-memory` | Need prior decisions, facts, or task context from AgentCore |
| `agentcore-code-graph` | Finding symbols, call paths, or ownership via the code graph |
| `agentcore-durable-write` | Persisting memory, task, activity, or decision records |
| `agentcore-documentation-authoring` | How to write docs; Full-tier Markdown law (required before product doc edits) |
| `agentcore-docs-sync` | Docs drift, coverage, Body-tier validate, note, draft, or index |
| `agentcore-create-task` | Creating a durable follow-up Task in AgentCore |
"""

_SKILLS: list[dict[str, Any]] = [
    {
        "name": "agentcore-session-bootstrap",
        "description": "Bootstrap an AgentCore MCP session—ping, profile, resolve guidance, then code.",
        "when_to_use": ["session-start", "mcp", "bootstrap"],
        "title": "AgentCore session bootstrap",
        "body": """---
name: agentcore-session-bootstrap
description: Bootstrap an AgentCore MCP session—ping, profile, resolve guidance, then code.
---

# AgentCore session bootstrap

## When

- Starting work on a project connected to AgentCore via MCP.
- After MCP reload or Usage Profile change.

## How

1. Via lazy MCP: `mcp_search_tools` then `mcp_execute_tool` — start with `agentcore_ping`.
2. Execute `agentcore_get_effective_profile` to see allowed capability tools.
3. Search/execute `agentcore_guidance_resolve` and apply `agents_entry` + `always_rules`.
4. If a catalog skill matches the user task, execute `agentcore_guidance_get_skill` before improvising.
5. For documentation questions or product Markdown work: `agentcore_docs_authoring_standards` + skill `agentcore-documentation-authoring`.
6. Only then start memory/graph/docs/write tools or local edits.

## Do not

- Start large refactors before guidance resolve when the tool is available.
- Assume tools exist without `mcp_search_tools` or the effective profile.
""",
    },
    {
        "name": "agentcore-memory",
        "description": "Retrieve or persist project memory through AgentCore MCP.",
        "when_to_use": ["memory", "recall", "remember"],
        "title": "AgentCore memory",
        "body": """---
name: agentcore-memory
description: Retrieve or persist project memory through AgentCore MCP.
---

# AgentCore memory

## When

- Need prior decisions, conventions, or facts for this project.
- User asks to remember or recall something durable.

## How

1. Retrieve with `agentcore_memory_retrieve` (`query`, optional `include_history`).
2. To persist a new fact, use `agentcore_write` with `resource=memory` (`title`, `body`, optional `tags`, `confidence`).
3. Cite what AgentCore returned; do not silently invent memory.

## Do not

- Keep durable project facts only in chat when write/retrieve tools are available.
""",
    },
    {
        "name": "agentcore-code-graph",
        "description": "Search AgentCore code knowledge graph before wide local search.",
        "when_to_use": ["code-graph", "symbols", "search"],
        "title": "AgentCore code graph",
        "body": """---
name: agentcore-code-graph
description: Search AgentCore code knowledge graph before wide local search.
---

# AgentCore code graph

## When

- Locating symbols, owners, callers, or related modules for a coding task.
- Planning a change and needing graph-guided context.

## How

1. Prefer `agentcore_code_graph_explore` for "how does X work", flows, or surveying an area (one call: seeds + call path + budgeted source).
2. Use `agentcore_code_graph_hybrid_search` or `agentcore_code_graph_search` for name/meaning lookup when you only need ids.
3. When you need related **human Markdown**, call `agentcore_docs_catalog` with tag/concern/lifecycle/query filters (cached lane enums + tag index). Then Read only the matched paths — do not invent DOCUMENTED_BY.
4. For a seed symbol, call `agentcore_code_graph_generation_context` and prefer `hybrid_documentation` (human → living → rationale → AST).
5. For reviews/PRs call `agentcore_code_graph_detect_changes` with changed file paths.
6. For architecture questions use `agentcore_code_graph_architecture_overview` or `agentcore_code_graph_path`.
7. Escalate to Read/`rg` only for pending-sync banners, low-confidence edges, or empty graph; report degraded mode when tools fail.

## Do not

- Prefer exhaustive workspace crawl when graph explore/search is available and healthy.
- Re-verify explore results with wide Grep when the pack already returned verbatim source.
- Treat docs catalog matches as graph edges; sync still owns DOCUMENTED_BY after evidence linked_symbols.
""",
    },
    {
        "name": "agentcore-durable-write",
        "description": "Write memory, task, activity, or decision records via AgentCore MCP.",
        "when_to_use": ["write", "persist", "decision", "activity"],
        "title": "AgentCore durable write",
        "body": """---
name: agentcore-durable-write
description: Write memory, task, activity, or decision records via AgentCore MCP.
---

# AgentCore durable write

## When

- Persisting a decision, activity note, memory, or task the project should retain.

## How

1. Call `agentcore_write` with `resource` in `memory` | `task` | `activity` | `decision`.
2. Fill the fields required for that resource (`title`/`body`/`instructions`/`summary` as applicable).
3. Confirm the tool result ids to the user when useful.

## Do not

- Fake success if the tool fails; surface the error and ask how to proceed.
""",
    },
    {
        "name": "agentcore-documentation-authoring",
        "description": (
            "Full-tier ThinkingSOC/AgentCore Markdown authoring law — call before writing "
            "or explaining product documentation."
        ),
        "when_to_use": [
            "documentation",
            "docs",
            "authoring",
            "standards",
            "frontmatter",
            "how-to-write-docs",
        ],
        "title": "AgentCore documentation authoring",
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
        "body": """---
name: agentcore-docs-sync
description: Run AgentCore docs-sync drift, status, Body-tier validate, note, draft, and index via MCP.
---

# AgentCore docs sync

## When

- Checking documentation drift or coverage (docs-as-code sync).
- Body-tier validate / note / draft / index via MCP.

## How

1. **Before writing or explaining product Markdown** under `docs/` (or other normative trees):
   execute `agentcore_docs_authoring_standards` and skill `agentcore-documentation-authoring`.
2. To find which docs to open (tags/lanes): `agentcore_docs_catalog` (optional `refresh`, filters).
3. Coverage / gaps: `agentcore_docs_status`.
4. Drift for a symbol: `agentcore_docs_drift_check` (`symbol`, optional `file_path`).
5. Write workflows: `agentcore_docs_write` with `mode` in `validate` | `note` | `draft` | `index`.
6. Keep committed documentation English per project laws.
7. After Full-tier edits on disk: gate with `agentcore docs-standards` / `agentcore quality-audit`; refresh catalog with `agentcore docs-catalog --refresh`.

## Do not

- Treat `agentcore_docs_write` mode=`validate` as Full-tier compliance for product docs.
- Bypass docs-sync for governed docs-as-code changes when these tools are on the profile.
- Skip `agentcore_docs_authoring_standards` when the user asks how documentation writing works.
- Invent DOCUMENTED_BY from catalog tags alone.
""",
    },
    {
        "name": "agentcore-create-task",
        "description": "Create a durable AgentCore Task for follow-up engineering work.",
        "when_to_use": ["task", "follow-up", "track"],
        "title": "AgentCore create task",
        "body": """---
name: agentcore-create-task
description: Create a durable AgentCore Task for follow-up engineering work.
---

# AgentCore create task

## When

- User or plan needs a durable follow-up Task tracked in AgentCore.

## How

1. Prefer `agentcore_create_task` with `title` and optional `instructions`.
2. Alternatively `agentcore_write` with `resource=task` when that path is required by profile docs.
3. Return the created task identity from the tool result.

## Do not

- Treat ephemeral chat checklists as a substitute for durable Tasks when the user asked to track work in AgentCore.
""",
    },
]


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
        },
    ]
    for skill in _SKILLS:
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
            }
        )
    return payloads
