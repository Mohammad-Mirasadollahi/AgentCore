# port_profile

Phase 8 shared helper for AgentCore development port profiles.

- Profile file: `backend/configs/port-profiles/agentcore-dev.json`
- Loads overrideable `AGENTCORE_*_PORT` values
- Rejects common default ports
- Optional bind check via `check_port_available`
