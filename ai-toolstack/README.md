# ThinkingSOC AI Toolstack

## Scope — Cursor IDE only (not product software)

`ai-toolstack/` configures **your Cursor development environment** on a machine that has cloned this repo. It is **not** part of the ThinkingSOC SOC platform: nothing here is deployed to production, started by the backend runner, or required for analysts to use the product.

| Belongs here | Does not belong here |
|--------------|----------------------|
| Rules, skills, `install.sh`, mcp-lazy, RTK, local agent memory under `data/` | Microservices, Nginx, databases, frontend runtime, `deploy-toolkit` releases |

**Product** architecture, APIs, and operations: [`backend/docs/`](../backend/docs/), [`frontend/docs/`](../frontend/docs/), root [`README.md`](../README.md).  
**Agents editing the repo** start at [`AGENTS.md`](../AGENTS.md) and this folder.

---

Cursor agent wiring: **Ponytail**, **mcp-lazy** (backends **memory** + **headroom**), **RTK**. Single Cursor MCP entry: **mcp-lazy** only.

**Rules are compact and non-duplicating:** Persian typography lives in **user-global** rules only; project `rules/*.mdc` own ThinkingSOC laws (cloud, root-cause, hub, ponytail, docs English, long jobs + scoped globs). Inventory: [`docs/cursor-rules-and-skills.md`](docs/cursor-rules-and-skills.md).

**Safe to push to GitHub** — configs, scripts, hooks, and rules are committed; machine-local agent runtime stays under `data/` (gitignored).

## Quick start (new clone)

```bash
cd /opt/ThinkingSOC

pipx install "headroom-ai[mcp]"   # install.sh can install this
./ai-toolstack/install.sh
npx mcp-lazy init
# Cursor → Reload Window

./ai-toolstack/scripts/run-tests.sh --quick
./ai-toolstack/scripts/ai-toolstack.sh verify --quick
```

**MCP in Cursor:** enable **mcp-lazy** only (`~/.cursor/mcp.json`). **memory** and **headroom** are backends in `data/local/mcp-lazy-servers.json`.

**Host auto-install:** `config/auto-install.env.sh` — when `AI_TOOLSTACK_AUTO_INSTALL=1` (default), `install.sh` installs missing **jq**, **pipx**, **RTK** (GitHub release), and optional **Node** (`AI_TOOLSTACK_AUTO_INSTALL_NODE=1`). Air-gap: set `AI_TOOLSTACK_AUTO_INSTALL=0` or `RTK_INSTALL_CMD` to a local path.

**AgentCore (`/opt/AgentCore`):** `./ai-toolstack/scripts/install-agentcore.sh` — sets `AI_TOOLSTACK_PROFILE=agentcore`, merges `config/auto-install-agentcore.env.sh` (Node + RTK auto-install on by default).

Refresh Ponytail vendor:

```bash
./ai-toolstack/scripts/sync-ponytail-vendor.sh
./ai-toolstack/install.sh
```

## What `install.sh` does

| Target | Source |
|--------|--------|
| `~/.cursor/mcp.json` | **mcp-lazy** only (memory + headroom backends in `mcp-lazy-servers.json`) |
| `~/.mcp-lazy/servers.json` | memory + headroom backends |
| `~/.cursor/hooks.json` | MCP toolchain + RTK + ponytail output stats |
| `.cursor/rules/*.mdc` | symlinks to `rules/` |
| `.cursor/skills/*` | symlinks to `skills/thinkingsoc`, `vendor/mattpocock`, `vendor/ponytail` |
| `.mcp-memory/` | symlink → `data/mcp-memory/` |

Implementation: thin entrypoint [`install.sh`](install.sh) sources [`lib/install/load.sh`](lib/install/load.sh) and modules under [`lib/install/`](lib/install/).

## Documentation

| File | Content |
|------|---------|
| [docs/token-optimization-overview.md](docs/token-optimization-overview.md) | **Agent base doc** |
| [docs/cursor-rules-and-skills.md](docs/cursor-rules-and-skills.md) | Rules + skills inventory |
| [docs/ponytail-cursor-stack.md](docs/ponytail-cursor-stack.md) | Ponytail + hooks |
| [docs/headroom-integration.md](docs/headroom-integration.md) | Compression lanes |
| [docs/llm-gateway-graphify-internal-task.md](docs/llm-gateway-graphify-internal-task.md) | Internal Gateway task (enrichment removed) |
| [../AGENTS.md](../AGENTS.md) | Agent quick reference |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/ai-toolstack.sh` | sync, stats, benchmark, verify, timer |
| `scripts/run-tests.sh` | Unit + verify smoke (`--quick`) |
| `scripts/verify-install.sh` | Post-install check |
| `scripts/sync-ponytail-vendor.sh` | Refresh upstream ponytail **skills** only (does not overwrite project `rules/ponytail.mdc`) |

