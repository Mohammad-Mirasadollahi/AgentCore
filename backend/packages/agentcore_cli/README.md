# agentcore CLI

Command-line interface for Usage Profiles, local project state, Cursor MCP export, and the MCP gateway.

Installed as console script `agentcore` via editable install (`pip install -e .` from repo root).

Layout: `main.py` (dispatch) · `parser.py` · `util.py` · `state.py` · `commands/` (handlers).

```bash
bash scripts/ensure-venv.sh
agentcore doctor
agentcore profile list
agentcore project register --tenant t --workspace w --project p --name Demo --usage-profile programming-cursor-mcp
agentcore project activate --tenant t --workspace w --project p --usage-profile programming-cursor-mcp
agentcore cursor export --tenant t --workspace w --project p --out /tmp/agentcore-mcp.json
agentcore mcp tools --usage-profile programming-cursor-mcp
```

Design: `docs/08-software-engineering-architecture/35-usage-profile-and-cursor-mcp-onboarding.md`  
CLI docs: `docs/08-software-engineering-architecture/36-agentcore-cli.md`
