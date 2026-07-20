# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root, or
- **`CONTEXT-MAP.md`** at the repo root if it exists — it points at one `CONTEXT.md` per context. Read each one relevant to the topic.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in. In multi-context repos, also check context-scoped ADR directories.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## ThinkingSOC layout (multi-context monorepo)

This repo does not yet have a root `CONTEXT.md`. Use the existing documentation graph as domain context until glossary files are created:

| Context | Primary docs | Notes |
|---------|--------------|-------|
| **Backend** | `backend/docs/` (standards, HLD, runbooks) | Microservices under `backend/services/`; Read design docs + scoped **`rg`** before edits |
| **Frontend** | `frontend/docs/` (NeonGlass UI, settings) | Read ui-standards; **`rg`** importers under `frontend/` |
| **Deploy / infra** | `deploy-toolkit/` | Release pipeline, 3-VM install |
| **Agent tooling** | `.cursor/rules/`, `.cursor/skills/`, `docs/agents/` | Cursor rules/skills and agent docs |

Entry points: [`AGENTS.md`](../../AGENTS.md), [`docs/agents/00-index.md`](00-index.md).

For standards-backed tasks, prefer **reading the relevant standards folder** then **narrow `rg`** — not repo-wide grep first.

## File structure (target)

Multi-context repo:

```
/
├── CONTEXT-MAP.md                     ← to be created by domain-modeling when needed
├── docs/adr/                          ← system-wide ADRs (when created)
├── docs/agents/                       ← Cursor agent documentation
├── .cursor/rules/                     ← Cursor rules (.mdc)
├── .cursor/skills/                    ← Cursor skills
├── backend/docs/                      ← backend standards & service design
└── frontend/docs/                     ← UI standards & system docs
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_
