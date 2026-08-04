# TLS edge (Caddy)

HTTPS termination in front of AgentCore MCP and connect APIs. Backends stay on loopback; clients hit one public hostname.

## Quick start

1. **Ensure certs** (auto-generates under `<AGENTCORE_DATA_ROOT>/certs/` when missing):

   ```bash
   export AGENTCORE_DATA_ROOT=/opt/AgentCore-data   # or your install data root
   export AGENTCORE_PUBLIC_HOSTNAME=agentcore.example.internal
   source scripts/install/tls_edge/ensure_certs.sh
   ```

   Operator-supplied paths win when both exist: `AGENTCORE_TLS_CERT` + `AGENTCORE_TLS_KEY`.

2. **Configure Caddy** — copy [`Caddyfile.example`](./Caddyfile.example), set hostname and cert env vars, start Caddy.

3. **Point clients** at `https://$AGENTCORE_PUBLIC_HOSTNAME` (MCP `/mcp`, connect APIs `/api/…`).

## Routing

| Path | Backend (loopback) |
| --- | --- |
| `/mcp*` | MCP HTTP (`AGENTCORE_MCP_HTTP_PORT`, default `32500`) |
| `/api/*` | Project-profile / connect API (`AGENTCORE_PROJECT_PROFILE_PORT`, default `32194`) |

Run `agentcore service start` (or Docker `mcp-gateway`) before the edge so backends are listening.

## Files

| File | Role |
| --- | --- |
| `ensure_certs.sh` | Calls `agentcore_cli.tls_certs.ensure_tls_material`; exports cert/key paths |
| `Caddyfile.example` | Example reverse-proxy site block |

Implementation: [`backend/packages/agentcore_cli/tls_certs.py`](../../../backend/packages/agentcore_cli/tls_certs.py).
