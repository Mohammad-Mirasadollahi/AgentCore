# unused_candidates

Graph-backed dead-code candidate discovery (scores + evidence). AgentCore never deletes files.

## Boundaries

- **May:** compute unused / unreachable / zombie / runtime-dead / flag-controlled rows; filter report pool via `path_prefix`.
- **Must not:** mutate the repo; treat Memory as candidate SoT; raise `safe_to_delete` via triage.

## Start here

1. `find.py` — orchestration + MCP payload (`find_unused_candidates`)
2. `liveness.py` — live roots / test_only / inbound edges
3. `findings.py` — unreachable_file, zombie_package, runtime_dead
4. `rows.py` — score + row shape
5. `../dead_code_scoring.py` — numeric score model
