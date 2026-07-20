# IDE agent documentation index

English-only. **This tree is Cursor IDE setup and agent behavior in this repo—not AgentCore product architecture.** Product specs live under [`../README.md`](../README.md) (phases 00–15).

**Canonical file:** this folder at repo root (`docs/agents/`).

## Reading order

| Step | Document | Why |
| --- | --- | --- |
| 1 | [`AGENTS.md`](../../AGENTS.md) | Entry: laws, high-signal skills |
| 2 | [`.cursor/rules/`](../../.cursor/rules/) | Always-apply / scoped Cursor rules (`.mdc`) |
| 3 | [`.cursor/skills/`](../../.cursor/skills/) · [`.agents/skills/`](../../.agents/skills/) | Agent skills (`SKILL.md`) |
| 4 | [`ide-mcp-first-workflow.md`](ide-mcp-first-workflow.md) | Docs-first discovery, live-test flow (if present) |
| 5 | [`ide-workspace-rule-discovery.md`](ide-workspace-rule-discovery.md) | Optional: org interview → workspace packs → `.mdc` (if present) |
| 6 | [`domain.md`](domain.md) | Monorepo context |
| 7 | [`issue-tracker.md`](issue-tracker.md) · [`triage-labels.md`](triage-labels.md) | Issue workflow vocabulary |

## Active Persian / language rules

| Path | Role |
| --- | --- |
| `.cursor/rules/persian-chat-typography.mdc` | RTL wrapper + right alignment (`alwaysApply`) |
| `.cursor/rules/reply-fa-code-docs-en.mdc` | Persian chat; English code/docs (`alwaysApply`) |
| `.cursor/skills/persian-chat-reply/SKILL.md` | Skill detailing the RTL reply pattern |

## Not for product implementation

| Need | Go to |
| --- | --- |
| Platform rule engine | `docs/04-rule-engine-orchestration/` |
| Product domain packs | `docs/08-software-engineering-architecture/26-domain-customization-and-feature-control.md` |
| Product AGENTS / rules / skills for connected coding agents | [`../15-agent-workspace-guidance/00-index.md`](../15-agent-workspace-guidance/00-index.md) |
| MCP-first seed skills (route work to AgentCore via MCP) | [`../15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md`](../15-agent-workspace-guidance/06-mcp-first-agent-skills-and-rules.md) |
| Backend | `backend/docs/` |

IDE `.mdc` configuration in this repository does **not** implement those product features.

## After changing rules/skills

Cursor → **Reload Window**.
