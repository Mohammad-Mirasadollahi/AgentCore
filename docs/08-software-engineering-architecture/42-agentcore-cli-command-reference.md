---
doc_id: ac.doc.sea.agentcore-cli-command-reference
title: 42 - AgentCore CLI Command Reference
doc_type: runbook
status: active
schema_version: '1.0'
owner: platform-product
summary: 'Operator reference for every agentcore subcommand: why it exists, required vs optional
  flags, examples, what files or stores change, and mandatory sync filter config (wildcards
  + built-in language excludes).'
tags:
- cli
- agentcore
- operator
- runbook
- mcp
phase: 08-software-engineering-architecture
canonical_path: docs/08-software-engineering-architecture/42-agentcore-cli-command-reference.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols:
- backend/packages/agentcore_cli/main.py::main
- backend/packages/agentcore_cli/sync_config.py::SyncConfigError
- backend/packages/agentcore_cli/software_paths.py::format_paths_env
- backend/packages/agentcore_cli/docs_link_sync.py::DocsLinkSyncResult
- backend/services/code-graph-service/src/code_graph_service/domain/repo_discovery.py::DiscoveredFile
- backend/services/code-graph-service/src/code_graph_service/domain/doc_discovery.py::DiscoveredDocFile
- backend/services/code-graph-service/src/code_graph_service/application/ingest/human_docs.py::human_doc_symbol_id
- backend/packages/agentcore_cli/cli_defaults.py::load_dotenv_files
- backend/packages/agentcore_cli/identity.py::identity_path
- tests/backend/services/code-graph-service/test_human_docs_ingest.py::login
- backend/packages/agentcore_cli/commands/sync.py::cmd_sync
- backend/packages/agentcore_cli/commands/docs_standards/cmd.py::cmd_docs_standards
- backend/packages/agentcore_cli/docs_link_sync.py::sync_human_docs
- backend/packages/agentcore_cli/commands/docs_standards/remediate.py::remediate_markdown_doc
placeholder: 1
doc_version: 1.1.0
updated_at: '2026-07-24'
---

# 42 - AgentCore CLI Command Reference

## Purpose

This document is the **canonical operator reference** for the `agentcore` CLI: every shipped subcommand, why it exists, which flags are required, a copy-paste example, and what changes on disk or in stores when you run it.

For install / PATH / package layout, see [36-agentcore-cli.md](./36-agentcore-cli.md). For remote MCP onboarding flows, see [41](./41-one-command-cross-platform-agent-onboarding.md). For **server/client upgrade** (`agentcore upgrade *`, `install.sh --upgrade`), see [51-software-upgrade-server-and-client.md](./51-software-upgrade-server-and-client.md).

## How to read each command

| Field | Meaning |
| --- | --- |
| **Why** | Problem this command solves (reason it exists) |
| **Required** | Flags / preconditions that must be present or the command exits |
| **Optional** | Common optional flags |
| **Example** | Typical invocation |
| **What changes** | Files, env, graph data, or processes affected |
| **If you change X** | What happens when you re-run with different IDs or flags |

## Scope IDs (tenant / workspace / project)

AgentCore isolates graph and project state by three string IDs:

| ID | Role |
| --- | --- |
| `tenant` | Org / customer boundary |
| `workspace` | Team or environment inside a tenant |
| `project` | One application / repo under a workspace |

**You choose these IDs.** Nothing mints a tenant id from your username. Use lowercase letters, digits, and hyphens (slug style), e.g. `acme`, `eng`, `payments`.

### Where IDs are set

| Step | Command / file | Sets |
| --- | --- | --- |
| First time (recommended) | `agentcore init --tenant … --workspace … --path …` | `~/.agentcore/identity.yaml`, repo `.env`, software `paths`, optional merge into `connect.yaml`, local project state |
| Connect config | `~/.agentcore/connect.yaml` → `scope:` | Used when identity/env do not already pin scope |
| Per-command override | `--tenant` / `--workspace` / `--project` | Highest priority for that run only |
| Env | `AGENTCORE_TENANT_ID`, `AGENTCORE_WORKSPACE_ID`, `AGENTCORE_PROJECT_ID` | After CLI flags; often written by `init` into `.env` |

### Resolution order (everyday commands)

For `status`, `sync`, `purge` (and other commands that call operator defaults):

1. CLI flags (`--tenant` / `--workspace` / `--project`)
2. Env (`AGENTCORE_*` from shell or loaded `.env` / `.env.local`)
3. `~/.agentcore/identity.yaml`
4. `~/.agentcore/connect.yaml` → `scope`
5. Dogfood defaults (`tenant=agentcore`, `workspace=dev`, `project=<cwd name>`)

**If you change IDs** (new `--tenant` / re-run `init --force` with different values): later `sync` / MCP tools read and write a **different scope**. Old graph data under the previous IDs remains until you `purge` that old scope (or wipe stores). IDE MCP configs keep the env baked in at `connect` time until you re-run `connect`.

### Required vs optional scope flags

| Command family | Scope flags |
| --- | --- |
| `init` | **`--tenant`, `--workspace`, and at least one `--path` required.** `--project` optional (default: current directory name) |
| `paths` | Uses active identity; `add` / `remove` take path arguments |
| `status` / `sync` / `purge` | Optional scope flags if identity/env/connect already set; `sync` uses pinned software paths |
| `inventory` | **No dashed mode flags.** Word modes only (`detail`, `save <path>`). Scope from identity/env/connect; uses pinned software paths |
| `docs-standards` | **No dashed mode flags.** Word modes only (`detail`, `save <path>`). Scans product Markdown under `docs/`, `backend/docs/`, `frontend/docs/`, and `deploy-toolkit/` (Full-tier gate + revision debt) |
| `docs-suggest-links` | Evidence-only `linked_symbols` suggestions from path citations. Flags: `--path`, `--docs-root`, `--include-all`, `--apply`, `--json`. Does **not** invent graph edges |
| `docs-catalog` | Cached frontmatter catalog from **observed** tags/lanes (not a global hardcoded enum). Flags: `--refresh`, `--roots`, `--tag`, `--concern`, … `--json` |
| `quality-audit` | **No dashed mode flags.** Word modes only (`detail`, `save [<path>]`). Categorized docs+code quality findings (incl. revision stamps); `save` defaults under `.agentcore/quality-audit/` |
| `stats` | **No dashed mode flags.** Word modes only (`detail`, `save <path>`). Scope from identity/env/connect; pinned software paths + sync filters |
| `project register|activate|show|effective` | **Required** (`--tenant` `--workspace` `--project`) |
| `cursor export`, `mcp serve`, `graph *`, `client wire-remote` | **Required** unless noted |

## First-time dogfood flow (same host)

```bash
cd /opt/AgentCore
bash install.sh                    # once
agentcore init --tenant acme --workspace eng --path /opt/AgentCore
agentcore connect --local
agentcore status
## Required before first sync:
## cp agentcore.sync.yaml.example agentcore.sync.yaml   # then edit (file is gitignored)
agentcore sync
```

| Step | Why |
| --- | --- |
| `init` | You pick durable IDs **and software path(s)** once so later commands stay short |
| `connect --local` | Write IDE MCP configs pointing at this checkout’s stdio gateway |
| `status` | Confirm Postgres/Neo4j/graph/MCP/paths before syncing |
| Sync filter file | `agentcore.sync.yaml` (or `.agentcore/sync.yaml`) must exist at each sync root — see [Sync filters](#sync-filters) |
| `sync` | Load each pinned software path into the code graph for that scope |

---

## Related Documents

- Continued in `docs/08-software-engineering-architecture/42-agentcore-cli-command-reference-continued.md`
- Upgrade CLI catalog: [51-software-upgrade-server-and-client.md](./51-software-upgrade-server-and-client.md#cli-catalog-agentcore-upgrade)
- Overview: [36-agentcore-cli.md](./36-agentcore-cli.md)
