# Cursor: MCP-first workflow (live test & feature QA)

Agents in ThinkingSOC use **repo docs + narrow `rg` / Read** before wide search, including for operational tasks (live test, smoke test, bring up services).

Enforced by **`ai-toolstack.mdc`** (docs-first discovery) and skill **`live-feature-qa`**. **Graphify and CRG were removed (2026-07).**

## Agent workflow (summary)

```
Read standards / runbooks → narrow rg → pytest → live smoke → fix
```

Optional MCP (enable **mcp-lazy** only in Cursor): **memory** (chat facts), **headroom** (compress large blobs) — both via `mcp_search_tools` / `mcp_execute_tool`, not separate Cursor servers.

Skill: `.cursor/skills/live-feature-qa/SKILL.md` (wired by `./ai-toolstack/install.sh`).

## Verify MCP is wired

```bash
./ai-toolstack/install.sh
npx mcp-lazy init
# Cursor → Reload Window
./ai-toolstack/scripts/ai-toolstack.sh verify --quick
```

In **Cursor → Settings → MCP**, enable **mcp-lazy** only. Do not add a standalone **headroom** server — Headroom is registered in `ai-toolstack/data/local/mcp-lazy-servers.json` and reached with `server_name: "headroom"`.

Generated file `~/.cursor/mcp.json` (symlink to `ai-toolstack/data/local/mcp.json`) must list **only** the `mcp-lazy` entry. See [`ai-toolstack/docs/headroom-integration.md`](../ai-toolstack/docs/headroom-integration.md).
