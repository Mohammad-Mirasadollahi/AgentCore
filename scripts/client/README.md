# Remote / one-command client

Full operator guide (SSH + HTTP, examples):  
[41-one-command-cross-platform-agent-onboarding.md](../../docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md)

SSH-only detail:  
[40-remote-dev-client-mcp-wiring.md](../../docs/08-software-engineering-architecture/40-remote-dev-client-mcp-wiring.md)

## Quick start

```bash
# Dev host — interactive SSH wizard (no connect.yaml required)
cd /opt/MyApp && agentcore connect

# Re-auth / replace AgentCore pubkey
agentcore connect --edit

# Advanced: template + hand-edit ~/.agentcore/connect.yaml
agentcore connect --init
```

```bash
# AgentCore server — HTTP mode only
export AGENTCORE_MCP_TOKEN_SECRET='long-random-secret'
export AGENTCORE_MCP_HTTP_PUBLIC_URL='http://agentcore.example.internal:32500'
agentcore mcp serve-http --port 32500
```
