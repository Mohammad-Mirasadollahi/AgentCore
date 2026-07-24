# Sync CLI package

## Purpose

Owns `agentcore sync` / `agentcore purge`: local stack sync, client remote SSH sync, and per-root ingest UI.

## Boundaries

- **May:** CLI orchestration, progress UI, usage logging, client→server SSH sync.
- **Must not:** Own graph store / ingest algorithms (those live in `code_graph_service`).

## Start here

1. `cmd.py` — entrypoints (`cmd_sync`, `cmd_purge`)
2. `one_root.py` — one software-path ingest + docs-link
3. `client_remote.py` — client checkout remote sync
4. `banner.py` / `report.py` — pre/post UI helpers
