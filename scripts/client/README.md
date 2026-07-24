# Remote / one-command client

Full operator guide (SSH + HTTP, examples):  
[41-one-command-cross-platform-agent-onboarding.md](../../docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md)

SSH-only detail:  
[40-remote-dev-client-mcp-wiring.md](../../docs/08-software-engineering-architecture/40-remote-dev-client-mcp-wiring.md)

## Quick start

```bash
# Dev host — interactive SSH wizard (cwd = that project for MCP + sync)
cd /opt/MyApp && agentcore connect

# Several apps at once (comma-separated); each gets MCP + sync pin
agentcore connect /opt/App1,/opt/App2,/opt/App3

# Re-auth / replace AgentCore pubkey
agentcore connect edit

# Advanced: template + hand-edit <checkout>/.agentcore/connect.yaml
agentcore connect init
```

```bash
# AgentCore server — HTTP mode only
export AGENTCORE_MCP_TOKEN_SECRET='long-random-secret'
export AGENTCORE_MCP_HTTP_PUBLIC_URL='http://agentcore.example.internal:32500'
agentcore mcp serve-http --port 32500
```
