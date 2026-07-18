# IDE agent documentation index

English-only. **This tree is compatible IDE setup and agent behavior in this repo—not AgentCore product architecture.** Product specs live under [`../README.md`](../README.md) (phases 00–14).

**Canonical file:** this folder at repo root (`docs/agents/`). The same files are mirrored under `ai-toolstack/docs/agents/`; `install.sh` syncs them here.

## Reading order

Follow this path when onboarding a machine or defining team-specific agent rules.

| Step | Document | Why |
| --- | --- | --- |
| 1 | [`AGENTS.md`](../../AGENTS.md) | Entry: install commands, high-signal skills |
| 2 | [`ai-toolstack/ide-agent-config/README.md`](../../ai-toolstack/ide-agent-config/README.md) | Where rules/skills live; one-command restore |
| 3 | [`ai-toolstack/docs/token-optimization-overview.md`](../../ai-toolstack/docs/token-optimization-overview.md) | MCP (mcp-lazy), memory, headroom, RTK |
| 4 | [`ai-toolstack/docs/IDE-rules-and-skills.md`](../../ai-toolstack/docs/IDE-rules-and-skills.md) | Rules vs skills; canonical rule list |
| 5 | [`ai-toolstack/docs/ponytail-IDE-stack.md`](../../ai-toolstack/docs/ponytail-IDE-stack.md) | Ponytail, terse output, Persian typography |
| 6 | [`ide-mcp-first-workflow.md`](ide-mcp-first-workflow.md) | Docs-first discovery, live-test flow |
| 7 | **[`ide-workspace-rule-discovery.md`](ide-workspace-rule-discovery.md)** | **Optional:** org interview → workspace packs → `.mdc` |
| 8 | [`domain.md`](domain.md) | Monorepo context (mattpocock engineering skills) |
| 9 | [`issue-tracker.md`](issue-tracker.md) · [`triage-labels.md`](triage-labels.md) | Issue workflow vocabulary |

## Workspace packs (step 7 output)

`ai-toolstack/ide-agent-config/workspace-packs/<slug>/` — see step 7 doc for activation (`install.sh` → Reload Window).

## Not for product implementation

| Need | Go to |
| --- | --- |
| Platform rule engine | `docs/04-rule-engine-orchestration/` |
| Product domain packs | `docs/08-software-engineering-architecture/26-domain-customization-and-feature-control.md` |
| Backend | `backend/docs/` |

IDE `.mdc` configuration does **not** implement those features.

## Quick commands

```bash
./ai-toolstack/scripts/install-agentcore.sh
# IDE → Reload Window
./ai-toolstack/scripts/ai-toolstack.sh verify --quick
```

Skill for step 7: `IDE-workspace-rule-discovery`.
