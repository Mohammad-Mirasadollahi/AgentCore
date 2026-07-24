---
name: agentcore-source-contracts
description: Selective module contract docstrings (49) and package README maps (50).
---

# AgentCore source contracts

## When

- Editing hard modules: queues, workers, dual-store durability, state machines, trust boundaries, fail-open/fail-closed.
- **Fix-on-read:** opened a hard module (49) with missing/wrong file-top contract.
- Agents confuse SoT / crash policy, or a package/folder seam ownership.
- Adding or splitting a service/shared package root.

## How

1. **Module contract (49)** — hard modules only: English file-top docstring, 3–6 lines: role; SoT/invariants; allowed vs forbidden failures (fail-open vs fail-closed). Optional wake/rebuild. Normative: `docs/08-software-engineering-architecture/49-module-contract-docstrings-standard.md`.
2. Read an existing contract before changing durability, retries, or crash handling.
3. Update or delete the header in the **same** change when the contract changes — never leave a lying header.
4. **Fix-on-read:** missing/wrong hard-module header → add/fix **same turn** before other work.
5. **Package README (50):** Purpose, Boundaries (may/must-not), Start-here list of 2–5 files. Soft ≤ ~40 lines. Normative: `docs/08-software-engineering-architecture/50-package-folder-readme-standard.md`.
6. After edits: prefer graph sync/ingest so `MODULE_CONTRACT` / package README nodes stay retrievable.

## Do not

- Contract every helper/DTO/`__init__` re-export.
- Skip fix-on-read for a hard module you already opened.
- Write a per-file encyclopedia in folder READMEs.
- Put SoT / fail-open policy only in the README — it belongs in the hard-module docstring.
- Persian in committed source or README maps.
