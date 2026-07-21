# Cursor Rules and Project Skills (ThinkingSOC)

**Scope:** Cursor IDE agent config for this repo — not product runtime.  
**Start:** [`token-optimization-overview.md`](token-optimization-overview.md) · [`ponytail-cursor-stack.md`](ponytail-cursor-stack.md).  
**MCP:** memory + headroom via **mcp-lazy** only.

## Purpose

Wire compact project laws + on-demand skills without duplicating user-global Persian typography.

## Layers

- **Project rules** — `ai-toolstack/rules/` → `.cursor/rules/` (laws always on; others by glob / agent request). Compact prose, no tables in rule bodies.
- **User global** — `cursor-agent-config/global-rules/` → `~/.cursor/rules/` (Persian typography + source English).
- **Skills** — `ai-toolstack/skills/` → `.cursor/skills/` (on demand).
- **Entry points** — `.cursorrules`, [`AGENTS.md`](../../AGENTS.md) (short pointers only).
- **Recovery** — [`cursor-agent-config/README.md`](../cursor-agent-config/README.md).

Edit under `ai-toolstack/`, then `./ai-toolstack/install.sh`. Inventory: [`MANIFEST.md`](../cursor-agent-config/MANIFEST.md).

## Ownership (no double context)

- Persian RTL/LTR → **user global only** (project rules may *name* the file, never paste the gate).
- Source-code English → **user global**.
- Repo **docs** English → project `code-and-docs-english-only.mdc`.
- YAGNI + terse English chat → project `ponytail.mdc` (ThinkingSOC-owned; vendor sync must not overwrite).

## Project rules

**Always on:** `no-cloud-exfiltration` · `root-cause-fix` · `ai-toolstack` (hub) · `ponytail` · `code-and-docs-english-only` (docs) · `long-job-progress-chat`.

**Scoped / agent-request:** `microservice-architecture` (`backend/**`) · `documentation-authoring` (docs trees) · `structured-logging` (backend Python) · `deploy-long-job-heartbeat` (`deploy-toolkit/**`) · `mcp-memory` (when using Memory).

**Removed:** `mcp-first-agent` (folded into hub) · `ponytail-stack-cursor` (merged into `ponytail`) · skill `ponytail-cursor-stack` (doc only: `ponytail-cursor-stack.md`) · Graphify/CRG rules.

## Skills

ThinkingSOC under `skills/thinkingsoc/` (e.g. `root-cause-fix`, `live-feature-qa`, `use-mcp-toolstack`, `write-documentation`, `deploy-release-pipeline`, …). Vendor ponytail under `skills/vendor/ponytail/`. Persian chat skill is **user-global only** (`cursor-agent-config/global-skills/`).

```bash
./ai-toolstack/scripts/sync-ponytail-vendor.sh   # skills only
./ai-toolstack/install.sh
```

## Install / verify

```bash
./ai-toolstack/install.sh && npx mcp-lazy init   # Reload Window
./ai-toolstack/scripts/run-tests.sh --quick
./ai-toolstack/scripts/ai-toolstack.sh verify [--quick]
```

## Rules vs skills

Always-on laws → **rules**. Feature runbooks / live QA → **skills**. Chat prefs across sessions → **MCP Memory** (not rules).

## Related

[`ponytail-cursor-stack.md`](ponytail-cursor-stack.md) · [`token-optimization-overview.md`](token-optimization-overview.md) · [`headroom-integration.md`](headroom-integration.md)
