"""Full-tier documentation authoring law for MCP-connected coding agents.

Single source of truth for:
- Seed skill `agentcore-documentation-authoring`
- MCP tool `agentcore_docs_authoring_standards` (maps_to docs_sync.authoring_standards)

Docs-sync Body-tier validate/note/draft/index is NOT sufficient for AgentCore product
docs under `docs/`. Agents must apply this Full-tier law when writing or remediating
those trees.
"""

from __future__ import annotations

from typing import Any

# Canonical paths (read on disk when available; this payload is always available via MCP).
CANONICAL_PATHS: dict[str, str] = {
    "portable_law": "docs/agents/documentation-authoring.md",
    "team_playbook": "docs/agents/team-documentation-playbook-for-agentcore.md",
    "team_handout": "docs/agents/TEAM-HANDOUT-agentcore-documentation-complete.md",
    "standardization_procedure": "docs/00-master-plan/10-documentation-standardization-procedure.md",
    "hybrid_coverage": "docs/07-code-knowledge-graph/41-hybrid-documentation-coverage.md",
    "docs_catalog": "docs/07-code-knowledge-graph/42-documentation-catalog-and-lane-cache.md",
    "standards_pack": "backend/docs/standards/documentation/",
    "pack_01": "backend/docs/standards/documentation/01-professional-documentation-standard.md",
    "pack_02": "backend/docs/standards/documentation/02-documentation-structure-and-machine-ingest-standard.md",
    "pack_03": "backend/docs/standards/documentation/03-documentation-classification-and-lanes.md",
    "pack_04": "backend/docs/standards/documentation/04-diagrams-and-agent-readable-flows.md",
    "write_documentation_skill": ".agents/skills/write-documentation/",
}

# Closed-set reminders; full enums live in pack 03 / procedure 09.
REQUIRED_FRONTMATTER_KEYS: list[str] = [
    "doc_id",
    "title",
    "doc_type",
    "status",
    "schema_version",
    "owner",
    "summary",
    "tags",
    "phase",
    "canonical_path",
    "lifecycle_lane",
    "concern_lane",
    "audience_lane",
    "authority",
    "visibility",
]

HARD_REQUIREMENTS: list[str] = [
    "English only in committed Markdown.",
    "Correct folder under docs/, backend/docs/, frontend/docs/, ai-toolstack/docs/, or deploy-toolkit.",
    "Full YAML frontmatter including all five lane fields (closed-set enums).",
    "doc_id form ac.doc.<domain>.<slug> for AgentCore docs/ (never tsoc.doc.* there).",
    "Exactly one H1 matching title; Purpose H2; chunkable H2s; Related Documents for normative types.",
    "Soft body budget ~400 lines, hard ~800 — split siblings when exceeded.",
    "Implementation-grade content (contracts, ownership, failure, verification) — not marketing.",
    "Design types (hld/lld/feature_spec/service_design): Mermaid + matching agent-readable flow table in the same H2.",
    "linked_symbols only when evidence exists on disk (qualified_name / path::Symbol / symbol id).",
    "Optional evidence helper: agentcore docs-suggest-links (dry-run; --apply only updates frontmatter; sync creates edges).",
    "Hybrid coverage optional layers prefer human → living → rationale → AST; never invent DOCUMENTED_BY (see docs/07-code-knowledge-graph/41-hybrid-documentation-coverage.md).",
    "Use docs catalog (agentcore docs-catalog / agentcore_docs_catalog) for tag/lane narrowing before reading many Markdown files.",
    "When standardizing or remediating: follow docs/00-master-plan/10-documentation-standardization-procedure.md.",
    "Fix-on-read: after opening a product Markdown file that fails Full-tier law, remediate that file in the same turn before continuing.",
    "Verify with CLI: agentcore docs-standards (zero issues) and agentcore quality-audit for docs.* categories.",
]

TIER_BOUNDARY: dict[str, str] = {
        "body_tier": (
            "Body-tier: docs-sync MCP validate/note/draft/index — thinner frontmatter for governed "
            "docs-as-code sync. Necessary for drift/coverage workflows; NOT Full-tier compliance."
        ),
        "full_tier": (
            "Full-tier: AgentCore product documentation under docs/ (and other normative trees). "
            "Requires portable law + packs 01–04 + procedure 10. MCP tool "
            "agentcore_docs_authoring_standards returns this checklist."
        ),
    }

CLI_GATES: list[str] = [
    "agentcore docs-standards",
    "agentcore docs-standards remediate (when remediating)",
    "agentcore docs-suggest-links (hybrid evidence linked_symbols suggestions)",
    "agentcore docs-catalog (tags/lanes cache for retrieval; --refresh after bulk doc edits)",
    "agentcore quality-audit (docs.* categories must be clean)",
]

SKILL_MARKDOWN = """---
name: agentcore-documentation-authoring
description: Full-tier ThinkingSOC/AgentCore Markdown authoring law for MCP coding agents.
---

# AgentCore documentation authoring (Full-tier)

## When

- User asks how documentation works, how to write docs, or what standards apply.
- Creating or materially editing Markdown under `docs/`, `backend/docs/`, `frontend/docs/`,
  `ai-toolstack/docs/`, or `deploy-toolkit/**/*.md`.
- Remediating nonconforming docs or bulk-standardizing product documentation.
- **Fix-on-read:** you Read a product Markdown file and it fails Full-tier law (frontmatter,
  structure, English, Purpose/H1, design Mermaid+flow, etc.).

## Mandatory first step (MCP)

1. Call `agentcore_docs_authoring_standards` and follow the returned checklist.
2. If repo files are available, also Read:
   - `docs/agents/team-documentation-playbook-for-agentcore.md` (team reading list)
   - `docs/agents/documentation-authoring.md`
   - `docs/00-master-plan/10-documentation-standardization-procedure.md`
   - `docs/00-master-plan/06-professional-documentation-standard.md`
   - `docs/00-master-plan/08-documentation-structure-and-machine-ingest-standard.md`
   - `docs/00-master-plan/09-documentation-classification-and-lanes.md`
   - `docs/07-code-knowledge-graph/41-hybrid-documentation-coverage.md` (hybrid layers)

## Hard requirements (summary)

1. English only in committed docs.
2. Full frontmatter: `doc_id`, `title`, `doc_type`, `status`, `schema_version`, `owner`,
   `summary`, `tags`, `phase`, `canonical_path`, plus lanes
   (`lifecycle_lane`, `concern_lane`, `audience_lane`, `authority`, `visibility`).
3. `doc_id` = `ac.doc.<domain>.<slug>` under AgentCore `docs/`.
4. One H1 = title; Purpose H2; modular H2s; Related Documents for normative types.
5. Soft ≤ ~400 body lines; hard ≤ ~800 or split.
6. Design docs: Mermaid + matching flow table in the same H2 (not Mermaid-only).
7. `linked_symbols` only with on-disk evidence (optional helper: `agentcore docs-suggest-links`).
8. Standardize via procedure 10; gate with `agentcore docs-standards` and
   `agentcore quality-audit`.
9. Hybrid coverage (optional layers): prefer human → living → rationale → AST; never invent edges
   (`docs/07-code-knowledge-graph/41-hybrid-documentation-coverage.md`).
10. Narrow docs with `agentcore_docs_catalog` / `agentcore docs-catalog` (tags + lane enums) before wide Read.
11. **Fix-on-read:** remediate a nonconforming product doc you already opened in the **same turn**
    before continuing other work.

## Body-tier vs Full-tier

- **Body-tier:** `agentcore_docs_write` validate/note/draft/index — docs-sync only.
- **Full-tier:** this skill + `agentcore_docs_authoring_standards` — required for product docs.

## Do not

- Treat docs-sync validate as Full-tier compliance.
- Invent Persian committed Markdown.
- Leave a reviewed or Read nonconforming doc unfixed in the same turn.
- Use `linked_symbols` without evidence.
- Invent `DOCUMENTED_BY` edges outside `agentcore sync` Phase 2 resolve.
"""


def authoring_law_payload() -> dict[str, Any]:
    """Structured payload for MCP tool agentcore_docs_authoring_standards."""
    return {
        "law_id": "agentcore.documentation_authoring.full_tier",
        "schema_version": "1.0",
        "summary": (
            "Full-tier documentation authoring law for AgentCore product Markdown. "
            "Docs-sync Body-tier tools alone are not sufficient."
        ),
        "tier_boundary": TIER_BOUNDARY,
        "canonical_paths": CANONICAL_PATHS,
        "required_frontmatter_keys": REQUIRED_FRONTMATTER_KEYS,
        "hard_requirements": HARD_REQUIREMENTS,
        "cli_gates": CLI_GATES,
        "skill_name": "agentcore-documentation-authoring",
        "related_mcp_tools": [
            "agentcore_docs_authoring_standards",
            "agentcore_docs_catalog",
            "agentcore_docs_status",
            "agentcore_docs_drift_check",
            "agentcore_docs_write",
            "agentcore_code_graph_generation_context",
            "agentcore_guidance_get_skill",
        ],
        "skill_markdown": SKILL_MARKDOWN,
    }
