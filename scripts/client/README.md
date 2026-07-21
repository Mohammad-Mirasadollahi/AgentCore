# Remote / one-command client

Full operator guide (SSH + HTTP, examples):  
[41-one-command-cross-platform-agent-onboarding.md](../../docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md)

SSH-only detail:  
[40-remote-dev-client-mcp-wiring.md](../../docs/08-software-engineering-architecture/40-remote-dev-client-mcp-wiring.md)

## Quick start

```bash
# Dev host
agentcore connect --init
# Edit ~/.agentcore/connect.yaml (use example hostnames from doc 41; replace with yours)
cd /opt/MyApp && agentcore connect
```

```bash
# AgentCore server — HTTP mode only
export AGENTCORE_MCP_TOKEN_SECRET='long-random-secret'
export AGENTCORE_MCP_HTTP_PUBLIC_URL='http://agentcore.example.internal:32500'
agentcore mcp serve-http --port 32500
```
