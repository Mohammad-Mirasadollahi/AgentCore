# Token Optimization — Agent Base Document

> **Audience:** Cursor agents — read each session before wide repo exploration.  
> **Not product docs:** Dev-machine Cursor tooling only.  
> **Stack:** Ponytail + mcp-lazy (memory, headroom) + RTK. Graph MCP removed.  
> **Rules inventory:** [`cursor-rules-and-skills.md`](cursor-rules-and-skills.md)

## Purpose

Keep agent context small: one owner per law, docs-first discovery, compress large tool output.

## Ownership (do not duplicate)

- **User-global:** Persian chat typography (+ English in source) — `cursor-agent-config/global-rules/`.
- **Project always-on:** cloud law, root-cause, hub, ponytail, repo-docs English, long-job progress — `ai-toolstack/rules/`.
- **Project scoped:** microservice arch, documentation authoring, structured logging, deploy heartbeat, mcp-memory.

## Mandate

1. No cloud exfiltration without explicit user consent (`no-cloud-exfiltration.mdc`).
2. Discovery: service design / standards first, then path-scoped `rg` — not repo-wide Grep.
3. Code: `ponytail.mdc` ladder; `rg` callers before backend edits.
4. MCP: **mcp-lazy** only → `mcp_search_tools` → `mcp_execute_tool` (memory, headroom).
5. Memory: chat facts only — never copy repo docs or source into Memory.

## Tools

- **Docs + rg** — standards, HLD/LLD, callers.
- **mcp-lazy** — on-demand MCP schemas.
- **Memory** — preferences / chat decisions not in git.
- **Headroom** — large Read/JSON/logs (~500+ tokens); never on RTK-marked shell output.
- **RTK** — auto shell compression (`git`, `pytest`, `docker`, …).

## Workflow

Classify owning service → read design → narrow `rg` → minimal edit (ponytail) → `bash Setup/run_pytest.sh` for that service → live via `live-feature-qa` when asked.

## CLI

```bash
./ai-toolstack/install.sh && npx mcp-lazy init
./ai-toolstack/scripts/ai-toolstack.sh verify [--quick]
./ai-toolstack/scripts/ai-toolstack.sh stats status|gain --since 24h
./ai-toolstack/scripts/ai-toolstack.sh benchmark all
./ai-toolstack/scripts/run-tests.sh --quick
```

## Related

[`ponytail-cursor-stack.md`](ponytail-cursor-stack.md) · [`headroom-integration.md`](headroom-integration.md) · [`model-invoked-skills-audit.md`](model-invoked-skills-audit.md) · skill `use-mcp-toolstack`
