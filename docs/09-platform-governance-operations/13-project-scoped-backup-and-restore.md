---
doc_id: ac.doc.ops.project-scoped-backup-and-restore
title: Project-Scoped Backup and Restore
doc_type: runbook
status: active
schema_version: '1.0'
owner: platform-ops
summary: Operator runbook for exporting and restoring one AgentCore project scope as a
  portable .acbak bundle across servers, including gates, MCP status/dry-run, and install
  verification.
tags:
- backup
- restore
- acbak
- ops
- cli
phase: 09-platform-governance-operations
canonical_path: docs/09-platform-governance-operations/13-project-scoped-backup-and-restore.md
lifecycle_lane: current
concern_lane: ops
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols:
- backend/packages/agentcore_backup/orchestrator.py::export_bundle
- backend/packages/agentcore_backup/orchestrator.py::restore_bundle
- backend/packages/agentcore_backup/orchestrator.py::dry_run_bundle
- backend/packages/agentcore_cli/commands/backup_cmd.py::cmd_backup_export
- backend/packages/agentcore_cli/commands/backup_cmd.py::cmd_backup_restore
- backend/services/mcp-gateway-service/src/mcp_gateway_service/backends/backup.py::backup_dry_run
related_docs:
- docs/superpowers/specs/2026-08-01-project-backup-restore-design.md
- docs/09-platform-governance-operations/04-data-retention-backup-and-disaster-recovery.md
- docs/13-technology-stack-and-platform-decisions/13-storage-ownership-matrix.md
- docs/08-software-engineering-architecture/42-agentcore-cli-command-reference-part-4.md
- backend/runbooks/backup-restore/README.md
doc_version: 1.1.0
updated_at: '2026-08-01'
---

# Project-Scoped Backup and Restore

## Purpose

Move **one** AgentCore project's analytical state between servers using a portable
`.acbak` archive. This is not full-platform disaster recovery; it is a scoped migrate
path for memories, core data, code graph, docs-sync, guidance, and related rows.

## Operator flow

```mermaid
flowchart LR
  Src[SourceServer] -->|backup_export| Bundle[.acbak]
  Bundle -->|copy| Dst[TargetServer]
  Dst -->|backup_validate| Gate[Gates]
  Gate -->|backup_restore| Stores[(PG_and_Neo4j)]
```

| Step | Actor | Action | Outcome |
| --- | --- | --- | --- |
| 1 | Operator | `agentcore backup export -o ./p.acbak` on source | Bundle written with checksums |
| 2 | Operator | Copy `.acbak` to target host | File available offline |
| 3 | Operator | `agentcore backup validate -i ./p.acbak` | Contract/checksum/schema gates |
| 4 | Operator | `agentcore backup dry-run -i ./p.acbak` | Conflict preview without writes |
| 5 | Operator | `agentcore backup restore -i ./p.acbak` | Import into empty scope |
| 6 | Operator | Or restore with `--replace --yes` | Wipe target scope then import |

## Commands

```bash
# Export active scope (or pass --tenant/--workspace/--project)
agentcore backup export -o ./project.acbak

agentcore backup validate -i ./project.acbak
agentcore backup dry-run -i ./project.acbak

# Empty target
agentcore backup restore -i ./project.acbak

# Non-empty target (destructive)
agentcore backup restore -i ./project.acbak --replace --yes

# Optional remap on restore
agentcore backup restore -i ./project.acbak \
  --remap-tenant NEW_T --remap-workspace NEW_W --remap-project NEW_P

agentcore backup status
```

Optional `--skip-contract` on `validate` / `dry-run` / `restore` skips only the
`contract_version` gate; checksums and schema fingerprint still apply.

## What is included

| Store | Content |
| --- | --- |
| `project_profile` | Scoped documents |
| `identity_access` | Project documents |
| `common_context` | Guidance documents |
| `core_data` | Tasks, decisions, activities, … |
| `memory` | Items, questions, batches, embeddings, embedding id map |
| `code_graph` | PG symbols/edges/embeddings + Neo4j nodes/relationships |
| `docs_sync` | Symbols, documents, anchors, drift, drafts |
| `rule_engine` | Rules and evaluation artifacts |
| `adapter` | Connector **metadata** only (no secrets) |
| `orchestration` | Scoped documents |
| `audit` / `reporting` | Scoped documents |
| `local` | `.agentcore/projects/...json` pin (no secrets) |

## What is excluded (v1)

- Broker/outbox replay and adapter delivery/dead-letter streams
- Connector credential material
- Full-server Postgres/Neo4j volume snapshots
- Per-row merge (only empty-target import or full scope replace)

## Gates and failure

| Gate | Behavior |
| --- | --- |
| Checksums | Fail before writes if any file mismatches |
| `contract_version` | Fail unless `--skip-contract` |
| Schema fingerprint | Host must have every table the bundle used |
| Target non-empty | Fail unless `--replace --yes` |
| Insert conflicts | Fail if rows cannot insert after wipe/remap |
| Remap plain PKs | When target scope differs, opaque text ids become `acbak:{tenant}/{workspace}/{project}:{id}` so same-server clone does not collide with source rows; `sym:`/`doc:`/`edge:` ids rewrite the embedded project segment |
| Neo4j | If `AGENTCORE_CODE_GRAPH_STORE=neo4j`, export refuses placeholder password; restore fails if relationships cannot bind; scope wipe deletes nodes in batches |
| Post-restore counts | Fail if imported counts fall short of manifest |

## MCP (agents)

| Tool | Role |
| --- | --- |
| `agentcore_backup_status` | Last local job summary under `<AGENTCORE_DATA_ROOT>/backup/` |
| `agentcore_backup_dry_run` | Validate a **server-local** `bundle_path`; no large file transfer |

Export/restore remain CLI-only (server / both install roles). Client-only hosts do not
expose `backup` in the thin CLI allowlist.

## Install verification

After `install.sh` / `ensure-venv.sh`, these must succeed on **server** / **both**:

```bash
python -c "import agentcore_backup; print(agentcore_backup.__name__)"
agentcore doctor   # import_agentcore_backup: true
agentcore backup status
agentcore mcp tools | grep agentcore_backup
```

Package ships via `pyproject.toml` (`agentcore_backup`) with `pip install -e .`.
Usage-profile tools ship with `backend/configs/usage-profiles/programming-cursor-mcp.json`.

## Related Documents

- [Design](../superpowers/specs/2026-08-01-project-backup-restore-design.md)
- [Data retention and DR](./04-data-retention-backup-and-disaster-recovery.md)
- [CLI command reference part 4](../08-software-engineering-architecture/42-agentcore-cli-command-reference-part-4.md)
- [Package runbook](../../backend/runbooks/backup-restore/README.md)
- [Storage ownership matrix](../13-technology-stack-and-platform-decisions/13-storage-ownership-matrix.md)
