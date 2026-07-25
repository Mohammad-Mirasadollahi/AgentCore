# agentcore_client

Thin CLI package for **client-only** AgentCore installs (`install.sh --role client`).

## Purpose

Expose only connect / Usage Profile / process-lifecycle commands so a laptop cannot run server-admin AgentCore operations. The PATH name on client-only hosts is **`agentcore-client`** (bare `agentcore` is not installed).

## Boundaries

| May | Must not |
| --- | --- |
| Parse allowlisted commands | Register `service`, `graph`, `mcp serve`, governance, … |
| Dispatch to shared `agentcore_cli` handlers | Call local graph purge when `connect.yaml` has SSH |
| Own the PATH name `agentcore-client` on `role=client` | Put bare `agentcore` on PATH for client-only; replace full CLI on `server` / `both` |

## Start here

| File | Role |
| --- | --- |
| `main.py` | Console entry `agentcore-client` |
| `parser.py` | Allowlisted argparse surface |
| `dispatch.py` | Route to `agentcore_cli.commands.*` |

Shared allowlist / full-CLI gate: `agentcore_cli/client_allowlist.py`.  
Remote purge: `agentcore_cli/connect_flow/remote_purge.py`.  
Spec: `docs/superpowers/specs/2026-07-25-thin-client-cli-design.md`.  
Operator docs: `docs/08-software-engineering-architecture/36-agentcore-cli.md`.
