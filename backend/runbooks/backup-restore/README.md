# Backup Restore

Path: `backend/runbooks/backup-restore`

## Purpose

Operator boundary for **project-scoped** backup and restore (`.acbak` bundles).

## Normative docs (read these)

| Doc | Role |
| --- | --- |
| [`docs/09-platform-governance-operations/13-project-scoped-backup-and-restore.md`](../../../docs/09-platform-governance-operations/13-project-scoped-backup-and-restore.md) | Operator runbook (commands, gates, install verify) |
| [`docs/superpowers/specs/2026-08-01-project-backup-restore-design.md`](../../../docs/superpowers/specs/2026-08-01-project-backup-restore-design.md) | Design / architecture |
| [`docs/09-platform-governance-operations/04-data-retention-backup-and-disaster-recovery.md`](../../../docs/09-platform-governance-operations/04-data-retention-backup-and-disaster-recovery.md) | Platform DR context |

## Commands (quick)

```bash
agentcore backup export --output ./project.acbak
agentcore backup validate --input ./project.acbak
agentcore backup dry-run --input ./project.acbak
agentcore backup restore --input ./project.acbak
agentcore backup restore --input ./project.acbak --replace --yes
agentcore backup restore --input ./project.acbak \
  --remap-tenant NEW_T --remap-workspace NEW_W --remap-project NEW_P
agentcore backup status
```

Gates: checksums, `contract_version` (optional `--skip-contract`), schema fingerprint,
post-restore row-count verification, Neo4j required when `AGENTCORE_CODE_GRAPH_STORE=neo4j`.

MCP (status / dry-run only): `agentcore_backup_status`, `agentcore_backup_dry_run`.

## Implementation home

| Piece | Path |
| --- | --- |
| Package | `backend/packages/agentcore_backup/` |
| Store ports | `backend/packages/agentcore_backup/ports.py` |
| CLI | `backend/packages/agentcore_cli/commands/backup_cmd.py` |
| Parser | `backend/packages/agentcore_cli/parser/backup.py` |
| MCP backends | `backend/services/mcp-gateway-service/src/mcp_gateway_service/backends/backup.py` |
| Usage profile tools | `backend/configs/usage-profiles/programming-cursor-mcp.json` |
| Tests | `tests/backend/unit/agentcore_backup/`, `tests/backend/integration/agentcore_backup/` |

## Install

Ships with the `agentcore` distribution (`pyproject.toml` package `agentcore_backup`).
Post-install checks: `import agentcore_backup` in `ensure-venv.sh` and `agentcore doctor`.

## Modular Boundary

Expose behavior through the CLI and `agentcore_backup` public APIs. Do not import
private internals from sibling service packages beyond documented store codecs.
