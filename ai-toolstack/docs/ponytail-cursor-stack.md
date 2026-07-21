# Ponytail + ThinkingSOC Cursor stack

[Ponytail](https://github.com/DietrichGebert/ponytail) replaces the former Caveman speech stack. Graph MCP / CRG are removed; discovery is repo docs + scoped `rg` / Read.

## Purpose

Minimum working code + terse chat, without duplicating user-global Persian typography into project rules.

## Layers

- **Project rule:** `ponytail.mdc` (YAGNI + English chat lite + pointers). ThinkingSOC owns this file.
- **User-global:** Persian RTL/LTR — `cursor-agent-config/global-rules/persian-chat-typography-global.mdc` + skill `persian-chat-reply`.
- **Skills:** vendor `ponytail*` + ThinkingSOC runbooks — on demand.
- **MCP:** mcp-lazy (memory, headroom).
- **RTK / Headroom:** shell vs large non-shell compression — see `ai-toolstack.mdc`.

## Ladder (code)

YAGNI → reuse in repo → stdlib/native/dep → one line if possible → minimum that works (never cut validation/security/a11y).

## Repo docs English

Project rule `code-and-docs-english-only.mdc` covers **committed docs only**. Source-code English is stated once in the user-global rule.

## Vendor refresh

Sync **skills only**. Does **not** overwrite `ai-toolstack/rules/ponytail.mdc` (upstream snapshot saved as `skills/vendor/ponytail/upstream-ponytail.mdc`).

```bash
./ai-toolstack/scripts/sync-ponytail-vendor.sh
./ai-toolstack/install.sh
./ai-toolstack/scripts/generate-cursor-agent-manifest.sh
```

## Token stats

Hook: `ai-toolstack/hooks/ponytail-output-stats.sh`. Disable: `AI_TOOLSTACK_PONYTAIL_STATS_HOOK=0 ./ai-toolstack/install.sh`.

See: [`cursor-rules-and-skills.md`](cursor-rules-and-skills.md), [`token-optimization-overview.md`](token-optimization-overview.md).
