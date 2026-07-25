# port_profile

Phase 8 shared helper for AgentCore development port profiles and GAP-T07 preflight.

- Profile file: `backend/configs/port-profiles/agentcore-dev.json`
- Loads overrideable `AGENTCORE_*_PORT` values
- Rejects common default ports
- Bind check via `check_port_available`
- Owning-process detection via Linux `ss` / `lsof` (`find_port_owner`)
- Alternate free port suggestion in the project range (`suggest_alternate_port`)
- Full preflight report + `.agentcore/run/port-map.json` artifact (`run_preflight` / `write_port_map`)
- CLI: `agentcore ports show|check [--write-map] [--allow-ours]`
