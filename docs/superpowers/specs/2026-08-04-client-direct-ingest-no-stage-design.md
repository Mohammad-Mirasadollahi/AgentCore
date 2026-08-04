---
doc_id: ac.spec.client-direct-ingest-no-stage
title: Client direct ingest without durable source stage
doc_type: design
status: active
schema_version: '1.0'
owner: platform-engineering
summary: Client sync pushes only file contents needed for graph ingest into AgentCore;
  no durable rsync mirror of the client checkout is created on the AgentCore host.
tags:
- design
- sync
- ingest
- client
phase: 08-software-engineering-architecture
canonical_path: docs/superpowers/specs/2026-08-04-client-direct-ingest-no-stage-design.md
lifecycle_lane: current
concern_lane: platform
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
doc_version: 1.3.1
updated_at: '2026-08-04'
linked_symbols:
- backend/packages/agentcore_cli/commands/sync/client_remote.py::cmd_sync_client_remote
- backend/packages/agentcore_cli/connect_flow/client_push.py::client_push_sync
- backend/packages/agentcore_cli/connect_flow/client_push.py::build_push_docs
- backend/packages/agentcore_cli/connect_flow/ingest.py::remote_ingest
- backend/packages/agentcore_cli/commands/ingest_push.py::cmd_ingest_push
- backend/services/code-graph-service/src/code_graph_service/application/ingest/pushed.py::ingest_pushed_sources
- backend/services/code-graph-service/src/code_graph_service/domain/path_safety.py::safe_repo_rel_path
- backend/services/code-graph-service/src/code_graph_service/api/ingest.py
- backend/services/code-graph-service/src/code_graph_service/api/auth.py::require_content_push_http_auth
---

# Client direct ingest without durable source stage

## Purpose

Client remote sync must not require a software checkout on the AgentCore host.
The client discovers local sources and sends **ingest payloads** (path + body)
to the server graph pipeline. Bytes may cross the wire for changed files; a
durable code tree on the server is out of scope.

## Approaches considered

| Option | Idea | Trade-off |
| --- | --- | --- |
| A — Rsync stage + remote `agentcore sync --path` | Copy tree then walk on server | Durable mirror; rejected |
| B — Ephemeral unpack on server, ingest, delete | Tar to temp then wipe | Still writes a tree; rejected |
| C — Content-push ingest (selected) | Client walks locally; server `ingest_file` on bodies | No durable tree |

**Recommendation:** C.

## Goal / non-goals

**Goals**

- `agentcore-client sync` (no CLI `--path`) content-pushes only.
- Transport: SSH BatchMode **or** private-LAN HTTP when `server.graph_url` + bearer
  token are set (HTTP preferred when both are configured).
- Unchanged bodies may be skipped via FILE content-hash comparison.
- Human Markdown docs may be pushed on the last batch (`docs[]` →
  `upsert_human_documentation`) when sync docs filters are enabled.
- Connect ingest uses the same content-push path (no on-server tree required).
- Deleted local files are pruned when the client sends `present_paths`.
- Explicit CLI `--path` remains for operators who already have a tree on the host
  (NFS/clone/dogfood; requires SSH).

**Non-goals**

- Opening Postgres/Neo4j ports to developer laptops.
- Changing MCP query tools or embedding model routing.
- Replacing same-host / dogfood `agentcore sync --path`.
- Durable rsync mirrors or `source.mirror` escape hatches.

## Architecture

```mermaid
flowchart TD
  client[Client checkout cwd]
  disc[Discover + sync filters]
  hash{Server FILE hashes?}
  pack[Build changed batches]
  ssh[SSH stdin to agentcore ingest-push]
  http[Optional HTTP ingest-push]
  svc[CodeGraphService.ingest_pushed_sources]
  graph[(Neo4j / Postgres graph)]

  client --> disc --> hash
  hash -->|skip stable| pack
  hash -->|first sync / miss| pack
  pack --> ssh --> svc
  pack --> http --> svc
  svc --> graph
```

| Step | Actor | Action | Outcome |
| --- | --- | --- | --- |
| 1 | CLI client | Resolve connect.yaml scope + cwd | No `source.server_path` required |
| 2 | CLI client | Discover sources (+ docs) with sync filters | Candidate relative paths |
| 3 | CLI client | Optional: fetch FILE hash map (HTTP or SSH) | Skip unchanged bodies |
| 4 | CLI client | POST/SSH batches of `{file_path, source}` | Wire payload |
| 5 | CLI client | Last batch: `present_paths` + optional `docs[]` | Prune + docs upsert |
| 6 | Server | `ingest_pushed_sources` (+ docs) | Graph updated |

## Service / CLI

- `CodeGraphService.ingest_pushed_sources`
- `POST /api/v1/projects/{id}/graph/ingest-push` (optional `docs`)
- `GET /api/v1/projects/{id}/graph/file-hashes`
- `GET /api/v1/llm/config` (HTTP cloud-LLM consent probe)
- `agentcore ingest-push` (stdin JSON) and `agentcore file-hashes`
- Connect: `server.graph_url` / `AGENTCORE_CONNECT_GRAPH_URL` + token

## Client remote sync

1. Load connect settings (SSH **or** `graph_url` + token).
2. Cloud-LLM consent on the local TTY (SSH probes remote llm config; HTTP uses
   `/api/v1/llm/config`, fail-closed to assume-cloud when probe fails).
3. Run content-push against cwd (sources + optional docs).
4. CLI `--path` → remote `agentcore sync --path` only (SSH required).

## Optional capabilities (shipped)

| Capability | Behavior |
| --- | --- |
| HTTP content-push | When `server.graph_url` + bearer token set, prefer HTTP over SSH for hashes + push |
| Docs push | `build_push_docs` → last-batch `docs[]` → server `upsert_human_documentation` |
| Connect content-push | `remote_ingest` / `should_ingest` use content-push when SSH or HTTP is ready |

## Security / sovereignty

- **Trust boundary:** SSH BatchMode key (same as remote sync) or bearer-auth HTTP on a
  private LAN. Do not expose graph `ingest-push` to the public internet.
- **HTTP auth:** `ingest-push` / `file-hashes` require `Authorization: Bearer` matching
  `AGENTCORE_CODE_GRAPH_HTTP_TOKEN` (or `AGENTCORE_CONNECT_TOKEN`). When unset, only
  loopback is accepted.
- **Path safety:** server rejects absolute paths, ``..``, and NUL; keys are
  repo-relative only (`safe_repo_rel_path`).
- **Bounds:** `max_files` / `max_file_bytes` enforced server-side; HTTP schema caps
  list/body sizes (including typed `docs[]` bodies).
- **Secrets floor:** client never pushes `.env*`, key/pem material, or common
  credential filenames into the graph.
- **No body logging:** CLI/HTTP must not print full file sources.
- **Cloud LLM:** local TTY consent before non-private embed/docs routes (existing gate).
- Payload stays on the private LAN / existing SSH trust boundary.

## Verification

- Unit: path traversal / absolute paths rejected; oversize soft-fails; secrets skipped client-side.
- Unit: pushed ingest without a disk tree; prune via `present_paths`; hash skip.
- Unit: HTTP bearer auth; typed docs push; HTTP preferred when `graph_url` set.
- Live: client without a server checkout updates the graph over SSH BatchMode only.
