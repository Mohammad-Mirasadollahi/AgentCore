# Connect flow package

## Purpose

Owns `agentcore connect` orchestration: reachability, API/SSH MCP wiring, remote sync/ingest, and post-connect summary UI.

## Boundaries

- **May:** Client↔server connect paths, local cloud-LLM consent before SSH sync, MCP fragment writes.
- **Must not:** Own graph ingest algorithms, LiteLLM routing, or connect.yaml schema parsing (`connect_config`).

## Start here

1. `run.py` — `run_connect` entrypoint
2. `source_path.py` — shared SSH `source.server_path` discovery (connect + client sync)
3. `remote_sync.py` — client `agentcore sync` over SSH + consent
4. `ssh.py` — SSH argv + remote path probes
5. `ingest.py` / `summary.py` — ingest helpers and connect UI
