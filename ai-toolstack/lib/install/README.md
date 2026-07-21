# ai-toolstack install modules

Entrypoint: [`../install.sh`](../install.sh) → [`load.sh`](load.sh).

| Module | Responsibility |
|--------|----------------|
| [`common.sh`](common.sh) | Logging, dirs, symlinks, templates, chmod, verify/check helpers |
| [`resolve-bins.sh`](resolve-bins.sh) | Locate `headroom` and `rtk` binaries |
| [`hooks.sh`](hooks.sh) | Patch `cursor-hooks.json` (RTK preToolUse, ponytail afterAgentResponse) |
| [`mcp-packages.sh`](mcp-packages.sh) | Local npm/pipx installs + mcp-lazy patches |
| [`mcp-config.sh`](mcp-config.sh) | Generate MCP JSON, host deps, mcp-lazy `init` cache |
| [`cursor-wiring.sh`](cursor-wiring.sh) | Rules/skills symlinks, manifest, AgentCore entrypoints |
| [`load.sh`](load.sh) | Source order + `install_main` orchestration |

Add new install steps in the smallest matching module; keep `install.sh` as flags + exit codes only.
