---
doc_id: ac.doc.sea.agentcore-cli
title: 36 - AgentCore CLI
doc_type: runbook
status: active
schema_version: '1.0'
owner: platform-product
summary: '`agentcore` is the operator/developer CLI for Usage Profiles, local project state,
  coding-agent MCP connection, graph sync/status, and the MCP gateway process.'
tags:
- cli
- agentcore
- operator
- install
phase: 08-software-engineering-architecture
canonical_path: docs/08-software-engineering-architecture/36-agentcore-cli.md
lifecycle_lane: current
concern_lane: ops
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols:
- backend/packages/agentcore_cli/main.py::main
- backend/packages/agentcore_cli/commands/sync.py::cmd_sync
- backend/packages/agentcore_cli/docs_link_sync.py::sync_human_docs
related_docs:
- docs/08-software-engineering-architecture/42-agentcore-cli-command-reference.md
- docs/08-software-engineering-architecture/39-local-install-runbook.md
- docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md
- docs/08-software-engineering-architecture/40-remote-dev-client-mcp-wiring.md
- docs/08-software-engineering-architecture/35-usage-profile-and-cursor-mcp-onboarding.md
doc_version: 1.3.0
audience:
- engineer
- operator
language: en
security_classification: internal
---

# 36 - AgentCore CLI

## Purpose

`agentcore` is the operator/developer CLI for Usage Profiles, local project state, coding-agent MCP connection, graph sync/status, and the MCP gateway process. It is installed into the project virtualenv and linked onto the user PATH.

**Full command catalog** (why each command exists, required vs optional flags, examples, and what changes when you run it):

→ **[42 - AgentCore CLI Command Reference](./42-agentcore-cli-command-reference.md)**

## Install (PATH)

Preferred (full local bootstrap including OS deps and Compose when needed):

```bash
bash install.sh
## or venv/PATH only:
bash install.sh --skip-infra
```

See [39-local-install-runbook.md](./39-local-install-runbook.md).

Venv-only helper (also used by install stage `02_venv`):

```bash
bash scripts/ensure-venv.sh
```

This will:

1. Create/refresh `.venv`
2. Install `requirements-dev.txt`
3. `pip install -e .` so `.venv/bin/agentcore` exists
4. Symlink `~/.local/bin/agentcore` → `.venv/bin/agentcore`
5. Append a PATH export to `~/.bashrc` or `~/.zshrc` when `~/.local/bin` is not already on PATH

Manual PATH install:

```bash
agentcore path install --shell-rc .bashrc
```

## Where you choose IDs

Tenant and workspace IDs are **chosen by you** (not auto-minted):

```bash
agentcore init --tenant acme --workspace eng --path .
## optional: --project payments   (default: current directory name)
```

That writes `~/.agentcore/identity.yaml`, repo `.env`, and pins software path(s) for `sync`. Details: [doc 42 § Scope IDs](./42-agentcore-cli-command-reference.md#scope-ids-tenant--workspace--project).

## First-time operator flow

```bash
agentcore init --tenant acme --workspace eng --path /opt/AgentCore
agentcore connect --local
agentcore status
cp agentcore.sync.yaml.example agentcore.sync.yaml   # required; local/gitignored
agentcore sync
```

`agentcore init` requires at least one `--path` (software root). Edit later: `agentcore paths list|add|remove` (remove warns that old graph data remains). Sync uses pinned paths unless you pass `--path` to override.

Everyday:

```bash
agentcore sync
agentcore purge --yes   # graph only
## agentcore destroy-profile --tenant acme --workspace eng --project agentcore
## (interactive: type two different confirmation phrases; does not delete source code)
```

## Command index (quick)

| Command | One-line purpose |
| --- | --- |
| `agentcore init` | You choose tenant + workspace IDs and software `--path`(s); save identity + `.env` |
| `agentcore paths` | List / add / remove pinned software roots (sync targets) |
| `agentcore status` | Scope, paths, infra, graph counts, MCP configs, hints |
| `agentcore inventory` | Code/docs done vs remaining for pinned software roots |
| `agentcore docs-standards` | Which `docs/` files fail documentation standards + percent |
| `agentcore stats` | Code/docs counts, language mix %, processed vs remaining |
| `agentcore connect` / `--init` / `--local` | Onboard coding agents from connect.yaml or same-host dogfood |
| `agentcore sync` / `purge` | Load or wipe project graph data (sync requires `agentcore.sync.yaml` + pinned paths) |
| `agentcore destroy-profile` | Delete this scope’s profile data (not source code); two typed confirmations |
| `agentcore list-profiles` | List local tenant/workspace/project profiles + active scope |
| `agentcore doctor` / `version` | Health / version |
| `agentcore profile *` | Usage Profile catalog |
| `agentcore project *` | Local project register / activate / show |
| `agentcore cursor export` | Export Cursor `mcpServers` fragment |
| `agentcore mcp tools` / `tokens` / `serve` / `serve-http` | List tools; estimate connect/usage tokens; run stdio or HTTP gateway |
| `agentcore client *` | Remote SSH wire / doctor / list MCP clients |
| `agentcore path install` | Symlink CLI onto `~/.local/bin` |
| `agentcore ports show` / `check` | Port profile preflight |
| `agentcore graph *` | Ingest, freshness, explore, hybrid, smoke, watch |

Every row above is expanded in [doc 42](./42-agentcore-cli-command-reference.md).

## Port preflight

Uses `backend/packages/port_profile` and the default profile at `backend/configs/port-profiles/agentcore-dev.json`.

```bash
agentcore ports show
agentcore ports check
```

`ports check` exits `0` when all ports are free, `1` on conflict. Env vars named like profile keys (e.g. `AGENTCORE_API_PORT`) override defaults.

## Implementation home

- Package: `backend/packages/agentcore_cli/`
- Entry point: `pyproject.toml` → `agentcore = agentcore_cli.main:main`
- Layout: `main.py` · `parser/` · `cli_defaults.py` · `identity.py` · `commands/`
- Local state: `.agentcore/projects/<tenant>/<workspace>/<project>.json`
- Identity: `~/.agentcore/identity.yaml`
- Sync filters: local `agentcore.sync.yaml` (**gitignored**); template `agentcore.sync.yaml.example` (tracked)
- Tests: `tests/backend/tools/agentcore-cli/`

## Related Documents

- [42-agentcore-cli-command-reference.md](./42-agentcore-cli-command-reference.md) — **full command reference**
- [44-mcp-token-accounting.md](./44-mcp-token-accounting.md) — MCP connect cost and usage history
- [39-local-install-runbook.md](./39-local-install-runbook.md)
- [41-one-command-cross-platform-agent-onboarding.md](./41-one-command-cross-platform-agent-onboarding.md)
- [40-remote-dev-client-mcp-wiring.md](./40-remote-dev-client-mcp-wiring.md)
- [35-usage-profile-and-cursor-mcp-onboarding.md](./35-usage-profile-and-cursor-mcp-onboarding.md)
- [../07-code-knowledge-graph/35-wedge-operator-connect-runbook.md](../07-code-knowledge-graph/35-wedge-operator-connect-runbook.md)
