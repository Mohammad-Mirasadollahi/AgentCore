"""Platform seed pack: MCP-first always-on rule, agents entry, and capability skills."""

from __future__ import annotations

from typing import Any

from common_context_service.documentation_authoring_law import SKILL_MARKDOWN as DOCUMENTATION_AUTHORING_SKILL_BODY

# Normative bodies aligned with docs/15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md

SEED_PACK_ID = "awg-seed-mcp-first-programming"
# Bump when rule/skill/entry bodies change so client store + disk refresh.
SEED_PACK_VERSION = "2026.07.23.4"

MCP_FIRST_RULE_BODY = """# MCP-first AgentCore

When this workspace is connected to AgentCore over MCP (lazy facade: `mcp_search_tools` → `mcp_execute_tool`):

1. Search then execute `agentcore_guidance_resolve` before substantive coding.
2. For capabilities AgentCore exposes on the active Usage Profile, prefer the matching MCP tool over inventing a local-only substitute.
3. Do not store project facts only in chat when `agentcore_write` or `agentcore_memory_retrieve` can persist or recall them.
4. Do not skip code-graph search when locating symbols AgentCore can index. Prefer structural tools (`callers` / directed `impact` / `community`) before wide Read/Grep; escalate via `explore` / hybrid when sparse or semantic.
5. Do not skip docs-sync tools when checking drift, coverage, or drafting docs AgentCore governs.
6. When implementing, replacing, or retiring behavior, remove orphaned predecessors in the **same change** after proof: unused imports, superseded symbols, exclusive tests, and stale re-exports. Prefer `agentcore_code_graph_unused_candidates` when listed; otherwise prove with graph explore + repository search. Skip anything marked live-until-proven (dynamic registries, public HTTP/IAM exports, `tsoc-defer`). AgentCore does not delete files — you do.
7. When the user asks how documentation works, or when writing/remediating product Markdown under `docs/` (or other normative doc trees): call `agentcore_docs_authoring_standards` and follow skill `agentcore-documentation-authoring`. Docs-sync `validate` is Body-tier only — not Full-tier compliance.
8. If a needed capability is missing from `mcp_search_tools` results, execute `agentcore_get_effective_profile`, report the gap, and ask before bypassing with unmanaged workflows.
9. Keep identifiers, paths, and committed docs in English; follow any other always-on project rules from the guidance bundle.
10. When editing **hard modules** (queues, dual-store durability, workers, state machines, trust boundaries, fail-open/fail-closed): read then keep/update a selective file-top **module contract docstring** (role + source of truth / invariants + allowed vs forbidden failures) per `docs/08-software-engineering-architecture/49-module-contract-docstrings-standard.md`. Skip trivial helpers. Follow skill `agentcore-source-contracts`.
11. When working at a **package/folder seam** agents confuse: ensure a short **README map** (purpose + boundaries + 2–5 start-here files) per `docs/08-software-engineering-architecture/50-package-folder-readme-standard.md` — never a per-file encyclopedia. Follow skill `agentcore-source-contracts`.
12. **Fix-on-read (docs):** After you Read product Markdown under `docs/` / `backend/docs/` / `frontend/docs/` / `ai-toolstack/docs/` / `deploy-toolkit` and it fails Full-tier authoring law (missing/wrong frontmatter, structure, English, Purpose/H1, design Mermaid+flow, etc.): load `agentcore-documentation-authoring` + `agentcore_docs_authoring_standards`, then remediate **that file in the same turn** before continuing other work. Do not leave a known nonconforming doc you already opened.
13. **Fix-on-read (module contracts):** After you Read a **hard module** (standard 49 triggers) that lacks an accurate file-top module contract docstring: load `agentcore-source-contracts` and add/fix the 3–6 line header **in the same turn** before continuing. Skip trivial helpers/DTOs/re-exports per 49 — do not stamp every file.
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
| `agentcore-remove-dead-code` | After replace/retire: prove and delete orphaned symbols, imports, tests |
| `agentcore-durable-write` | Persisting memory, task, activity, or decision records |
| `agentcore-documentation-authoring` | Full-tier Markdown law; required on write **and** fix-on-read of nonconforming product docs |
| `agentcore-docs-sync` | Docs drift, coverage, Body-tier validate, note, draft, or index |
| `agentcore-source-contracts` | Hard-module contracts (49) + package README maps (50); fix-on-read when header missing |
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
6. For hard-module or package-folder ownership work: skill `agentcore-source-contracts` (standards 49/50).
7. Only then start memory/graph/docs/write tools or local edits.

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

1. For **who calls X / blast radius / community / outbound path** first use structural tools:
   `agentcore_code_graph_callers`, `agentcore_code_graph_impact` (set `direction`),
   `agentcore_code_graph_community`, or `agentcore_code_graph_call_path`. Prefer these before wide Read/`rg`.
   Structural payloads use `reference_kind=structural` — not IDE find-all-refs.
2. Prefer `agentcore_code_graph_explore` for "how does X work", flows, or surveying an area (one call: seeds + call path + budgeted source) when structural tools are sparse or the question is semantic — follow any `escalate_hint.next_tools` in payloads.
3. Use `agentcore_code_graph_hybrid_search` or `agentcore_code_graph_search` for name/meaning lookup when you only need ids.
4. When you need related **human Markdown**, call `agentcore_docs_catalog` with tag/concern/lifecycle/query filters (cached lane enums + tag index). Then Read only the matched paths — do not invent DOCUMENTED_BY.
5. For a seed symbol, call `agentcore_code_graph_generation_context` and prefer `hybrid_documentation` (human → living → rationale → AST).
6. For reviews/PRs call `agentcore_code_graph_detect_changes` with changed file paths.
7. For architecture questions use `agentcore_code_graph_architecture_overview` or `agentcore_code_graph_path`.
8. For **IDE-precise** rename / find-references / go-to-definition (local language servers only), use
   `agentcore_code_graph_ide_references`, `agentcore_code_graph_ide_definition`, or
   `agentcore_code_graph_ide_rename` (`reference_kind=ide_semantic`). After edits, rely on
   rename's built-in reconcile or call `agentcore_code_graph_reconcile_after_edit` — never write
   durable `CODE_REL` from LSP. If tools return `available=false`, install/configure `AGENTCORE_LSP_CMD_*`.
9. Escalate to Read/`rg` only for pending-sync banners, low-confidence edges, empty graph, or after structural + explore/hybrid; report degraded mode when tools fail.
10. After replacing or retiring symbols, open `agentcore-remove-dead-code` for orphan cleanup in the same change.
11. Prefer hybrid packs that surface module-contract rationale (`MODULE_CONTRACT`) and near-code package README maps after sync — they encode SoT/fail policy for hard modules.

## Do not

- Prefer exhaustive workspace crawl when graph structural/explore/search is available and healthy.
- Re-verify explore results with wide Grep when the pack already returned verbatim source.
- Treat docs catalog matches as graph edges; sync still owns DOCUMENTED_BY after evidence linked_symbols.
- Skip `escalate_hint` and jump straight to dumping full files.
- Confuse structural neighbors with IDE find-references, or dual-write LSP hits into the durable graph.""",
    },
    {
        "name": "agentcore-remove-dead-code",
        "description": "Prove and delete orphaned symbols, imports, and exclusive tests after a replace or retire.",
        "when_to_use": ["dead-code", "unused", "cleanup", "orphan"],
        "title": "AgentCore remove dead code",
        "body": """---
name: agentcore-remove-dead-code
description: Prove and delete orphaned symbols, imports, and exclusive tests after a replace or retire.
---

# AgentCore remove dead code

## When

- You implemented, replaced, or retired behavior and old symbols, imports, re-exports, or exclusive tests may remain.
- User asks to clean unused code in the scope you already touched.
- Unused-candidate MCP or graph explore shows safe-to-delete items in the task neighborhood.

## How

1. Prefer `agentcore_code_graph_unused_candidates` when listed (`scope_mode=changed_symbols` or task neighborhood). If missing, use explore + repository search (`rg`) for bare names and import paths.
2. Treat each candidate as **live until proven** otherwise: check dynamic loaders, string registries, public HTTP/IAM/SDK exports, tests-only refs, entrypoints, and `tsoc-defer` stopgaps.
3. Delete only what you can prove unused. Remove the symbol **and** its exclusive tests, fixtures, barrels, and docs that only described it.
4. Do not widen into unrelated refactors or repo-wide deletion hunts.
5. Verify with the smallest check that would fail if the delete were wrong.
6. Optionally `agentcore_write` Activity/WorkLog fields for paths removed so cleanup KPIs can attribute the task.
7. List skipped uncertain symbols with blockers in the chat summary.

## Do not

- Ask AgentCore to delete files; AgentCore only surfaces candidates and guidance.
- Delete public APIs, plugin hooks, or deferred stopgaps without an explicit root-cause fix.
- Count blind deletes (no proof, no verify) as successful cleanup.
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
        "body": """---
name: agentcore-source-contracts
description: Selective module contract docstrings (49) and package README maps (50).
---

# AgentCore source contracts

## When

- Editing queues, workers, dual-store durability, state machines, trust boundaries, or fail-open/fail-closed seams.
- **Fix-on-read:** you opened a hard module (standard 49) and the file-top contract docstring is missing or inaccurate.
- Agents repeatedly mis-edit a module's source of truth or crash policy.
- Working at a package/folder seam (application vs infrastructure, which folder owns rebuild).
- Adding or splitting a service/shared package root.

## How

1. **Module contract (49):** For hard modules only — file-top English docstring, 3–6 lines covering:
   - Role (what this module owns)
   - Source of truth / invariants
   - Allowed vs forbidden failures (fail-open vs fail-closed)
   Optional wake/rebuild line. Normative: `docs/08-software-engineering-architecture/49-module-contract-docstrings-standard.md`.
2. Read an existing contract docstring before simplifying durability, retries, or crash handling.
3. Update or delete the header in the **same** change when the contract changes; never leave a lying header.
4. **Fix-on-read:** if Read shows a hard module without an accurate header, add/fix it in the **same turn** before continuing other work.
5. **Package README (50):** Short ownership map only — Purpose, Boundaries (may/must-not), Start-here table with 2–5 entry/hard files. Soft ≤ ~40 lines. Normative: `docs/08-software-engineering-architecture/50-package-folder-readme-standard.md`.
6. After writing contracts/maps: prefer `agentcore_code_graph_sync` / ingest so FILE `ai_documentation`, MODULE_CONTRACT rationale, and package README nodes help retrieval.

## Do not

- Put a module contract on every helper/DTO/`__init__` re-export.
- Skip fix-on-read for a hard module you already opened with a missing/wrong header.
- Write a per-file encyclopedia in folder READMEs.
- Put SoT / fail-open policy only in the README — that belongs in the hard module docstring.
- Use Persian in committed source or README maps.
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
