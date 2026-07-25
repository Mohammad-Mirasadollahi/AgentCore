---
doc_id: ac.doc.sea.agentcore-cli
title: 36 - AgentCore CLI
doc_type: runbook
status: active
schema_version: '1.0'
owner: platform-product
summary: '`agentcore` is the operator/developer CLI. Server/both installs get the full surface;
  client-only installs use the thin `agentcore-client` entry (PATH still named `agentcore`) for
  connect, profile, and process control against a remote AgentCore server.'
tags:
- cli
- agentcore
- operator
- install
- client
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
- backend/packages/agentcore_client/main.py::main
- backend/packages/agentcore_cli/client_allowlist.py::CLIENT_TOP_LEVEL_COMMANDS
- backend/packages/agentcore_cli/commands/sync/cmd.py::cmd_sync
- backend/packages/agentcore_cli/docs_link_sync.py::sync_human_docs
related_docs:
- docs/08-software-engineering-architecture/42-agentcore-cli-command-reference.md
- docs/08-software-engineering-architecture/39-local-install-runbook.md
- docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md
- docs/08-software-engineering-architecture/40-remote-dev-client-mcp-wiring.md
- docs/08-software-engineering-architecture/35-usage-profile-and-cursor-mcp-onboarding.md
- docs/08-software-engineering-architecture/51-software-upgrade-server-and-client.md
- docs/superpowers/specs/2026-07-25-thin-client-cli-design.md
doc_version: 1.1.1
audience:
- engineer
- operator
language: en
security_classification: internal
updated_at: '2026-07-25'
---

# 36 - AgentCore CLI

## Purpose

`agentcore` is the operator/developer CLI for Usage Profiles, local project state, coding-agent MCP connection, graph sync/status, and (on server installs) the MCP gateway and stack. It is installed into the project virtualenv and linked onto the user PATH.

**Install roles and CLI surface:**

| Role | PATH CLI name | Surface |
| --- | --- | --- |
| `server` / `both` | `agentcore` only (full `agentcore_cli`) | Full catalog; includes client workflows — no `agentcore-client` on PATH |
| `client` | `agentcore-client` only (thin `agentcore_client`) | Allowlist only; bare `agentcore` is **not** installed on PATH |

Client-only `purge` / `sync` / `status` run against the AgentCore **server** over SSH using `connect.yaml` scope (fail-closed if CLI scope flags disagree). Design SoT: [thin-client CLI design](../superpowers/specs/2026-07-25-thin-client-cli-design.md).

**Full command catalog** (why each command exists, required vs optional flags, examples, and what changes when you run it):

→ **[42 - AgentCore CLI Command Reference](./42-agentcore-cli-command-reference.md)**

## Install (PATH)

Preferred (full local bootstrap including OS deps and Compose when needed):

```bash
bash install.sh
## or client-only (venv/PATH; thin CLI):
bash install.sh --role client
## alias:
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
3. `pip install -e .` so `.venv/bin/agentcore` and `.venv/bin/agentcore-client` exist
4. Symlink `~/.local/bin/agentcore` (server/both) or `~/.local/bin/agentcore-client` (client-only); remove the opposite name if present
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

Full CLI (`server` / `both`). On **client-only**, only the rows marked **client** appear in `--help`.

| Command | One-line purpose | Client-only |
| --- | --- | --- |
| `agentcore init` | You choose tenant + workspace IDs and software `--path`(s); save identity + `.env` | no |
| `agentcore paths` | List / add / remove pinned software roots (sync targets) | no |
| `agentcore status` | Scope, paths, infra, graph counts, MCP configs, hints (proxies to server on client) | **yes** |
| `agentcore inventory` | Code/docs done vs remaining for pinned software roots | no |
| `agentcore docs-standards` | Which `docs/` files fail documentation standards + percent | no |
| `agentcore stats` | Code/docs counts, language mix %, processed vs remaining | no |
| `agentcore connect` / `init` / `--local` | Onboard coding agents from connect.yaml or same-host dogfood | **yes** |
| `agentcore sync` / `purge` | Load or wipe project graph data (client: remote SSH, scope locked to connect.yaml) | **yes** |
| `agentcore destroy-profile` | Delete this scope’s profile data (not source code); two typed confirmations | no |
| `agentcore list-profiles` | List local tenant/workspace/project profiles + active scope | no |
| `agentcore doctor` / `version` | Health / version | **yes** |
| `agentcore profile *` | Usage Profile catalog | **yes** |
| `agentcore project *` | Local project register / activate / show | **yes** |
| `agentcore cursor export` | Export Cursor `mcpServers` fragment | no |
| `agentcore mcp tools` / `tokens` / `serve` / `serve-http` | List tools; estimate connect/usage tokens; run stdio or HTTP gateway | no |
| `agentcore client *` | Remote SSH wire / doctor / list MCP clients | **yes** |
| `agentcore path install` | Symlink CLI onto `~/.local/bin` (thin vs full by role) | **yes** |
| `agentcore ports show` / `check` | Port profile preflight | no |
| `agentcore graph *` | Ingest, freshness, explore, hybrid, smoke, watch | no |
| `agentcore upgrade *` | Server/client upgrade, contract check, control-plane jobs | `upgrade client` only |

Every row above is expanded in [doc 42](./42-agentcore-cli-command-reference.md). Upgrade details: [51 - Software Upgrade Server And Client](./51-software-upgrade-server-and-client.md).

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
- [51-software-upgrade-server-and-client.md](./51-software-upgrade-server-and-client.md) — server/client upgrade + `agentcore upgrade` catalog
- [44-mcp-token-accounting.md](./44-mcp-token-accounting.md) — MCP connect cost and usage history
- [39-local-install-runbook.md](./39-local-install-runbook.md)
- [41-one-command-cross-platform-agent-onboarding.md](./41-one-command-cross-platform-agent-onboarding.md)
- [40-remote-dev-client-mcp-wiring.md](./40-remote-dev-client-mcp-wiring.md)
- [35-usage-profile-and-cursor-mcp-onboarding.md](./35-usage-profile-and-cursor-mcp-onboarding.md)
- [../07-code-knowledge-graph/35-wedge-operator-connect-runbook.md](../07-code-knowledge-graph/35-wedge-operator-connect-runbook.md)
