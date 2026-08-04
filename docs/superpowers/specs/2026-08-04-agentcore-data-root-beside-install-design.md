---
doc_id: ac.spec.data-root-beside-install
title: AgentCore data root beside install
doc_type: design
status: active
schema_version: '1.0'
owner: platform-engineering
summary: Durable AgentCore data (Postgres, Neo4j, staged sources, usage logs, cache,
  backup metadata) lives in a sibling directory of the install root (default
  AgentCore-data), not Docker anonymous volume storage or /var/lib/agentcore.
tags:
- design
- data
- compose
- install
phase: 08-software-engineering-architecture
canonical_path: docs/superpowers/specs/2026-08-04-agentcore-data-root-beside-install-design.md
lifecycle_lane: current
concern_lane: platform
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
doc_version: 1.2.0
updated_at: '2026-08-04'
linked_symbols:
- backend/packages/agentcore_cli/data_root.py::resolve_data_root
- backend/packages/agentcore_cli/data_root.py::ensure_data_root
- backend/packages/agentcore_cli/data_root.py::discover_remote_data_root
- backend/packages/agentcore_cli/data_root.py::stamp_data_root
- scripts/install/common.sh::resolve_install_data_root
- backend/deployments/compose/compose.yaml
---

# AgentCore data root beside install

## Goal

Keep durable runtime data next to the AgentCore install tree so operators can
back up, move, or wipe data without hunting Docker volume IDs or `/var/lib`.

## Layout

Given install root `/opt/AgentCore` (or any `AGENTCORE_ROOT`):

```text
/opt/AgentCore/                 # code, .venv, lightweight .agentcore
/opt/AgentCore-data/            # default sibling: <basename>-data
  postgres/                     # Compose bind → container /var/lib/postgresql
  neo4j/                        # Compose bind → container /data
  sources/<project>/            # client remote sync rsync stage target
  backup/                       # backup job metadata (+ archives when local)
  cache/                        # docs-catalog and similar caches
  mcp-usage/                    # MCP usage JSONL
  sync-usage/                   # sync usage reports
```

Override: `AGENTCORE_DATA_ROOT` or install flag `--data-root PATH`. Interactive
server/both install prompts with Enter = sibling default; choice is persisted as
`data_root=` in `.agentcore/install-state.env`.

## Stays under install `.agentcore/`

`install-state.env`, `install-root`, `identity.yaml`, `connect.yaml`,
`upgrade-jobs/`, `upgrade-backups/`, `upgrade-evidence/`, `run/` (pids/logs),
`mcp-http.secret`, `projects/` registry JSON.

## Resolver

`resolve_data_root(install_root)`:

1. `AGENTCORE_DATA_ROOT` if set
2. else `<install>/.agentcore/data-root` marker
3. else `<parent>/<install_basename>-data`

`ensure_data_root` creates the subdirs, stamps the marker, and one-shot copies
legacy nonempty `.agentcore/{backup,cache,mcp-usage,sync-usage}` into the data
root when those dest dirs are empty.

Remote client stage reads the server marker (or `data_root=` in
`install-state.env`) over SSH so custom `--data-root` installs stage correctly.

## Compose

Replace named Docker volumes with bind mounts driven by `AGENTCORE_DATA_ROOT`.

## Migration

On first bring-up, if bind dirs are empty and legacy named volumes
`agentcore_agentcore-postgres-data` / `agentcore_agentcore-neo4j-data` exist,
copy volume contents into the bind dirs once (best-effort). Never delete the
old volumes automatically.

## Non-goals

- Moving upgrade job state out of `.agentcore`
- Changing Postgres/Neo4j ports or credentials
- Client-only hosts creating Compose data dirs
