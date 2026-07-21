# Model-invoked skills audit

Generated from `ai-toolstack/skills`, `ai-toolstack/cursor-agent-config/global-skills`.

Skills **without** `disable-model-invocation: true` expose `description` to the agent every turn (context load). Trim: set `disable-model-invocation: true` for `/command`-only skills you invoke manually.

| Count | Mode |
|-------|------|
| 26 | model-invoked (costs context) |
| 29 | user-only (no description in window) |

## Model-invoked (sorted by description length)

| Skill | ~desc chars | Path | Trim hint |
|-------|-------------|------|-----------|
| `ponytail` | 825 | `ai-toolstack/skills/vendor/ponytail/ponytail/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `remove-dead-code` | 584 | `ai-toolstack/skills/thinkingsoc/remove-dead-code/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `ponytail-review` | 456 | `ai-toolstack/skills/vendor/ponytail/ponytail-review/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `review` | 417 | `ai-toolstack/skills/vendor/mattpocock/review/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `doc-driven-implementation` | 364 | `ai-toolstack/skills/thinkingsoc/doc-driven-implementation/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `implement-backend-service-change` | 294 | `ai-toolstack/skills/thinkingsoc/implement-backend-service-change/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `qa` | 281 | `ai-toolstack/skills/vendor/mattpocock/qa/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `codebase-design` | 265 | `ai-toolstack/skills/vendor/mattpocock/codebase-design/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `root-cause-fix` | 256 | `ai-toolstack/skills/thinkingsoc/root-cause-fix/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `deploy-release-pipeline` | 254 | `ai-toolstack/skills/thinkingsoc/deploy-release-pipeline/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `write-documentation` | 251 | `ai-toolstack/skills/thinkingsoc/write-documentation/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `frontend-neon-glass-page` | 233 | `ai-toolstack/skills/thinkingsoc/frontend-neon-glass-page/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `tsoc-source-comments` | 231 | `ai-toolstack/skills/thinkingsoc/tsoc-source-comments/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `live-feature-qa` | 223 | `ai-toolstack/skills/thinkingsoc/live-feature-qa/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `domain-modeling` | 216 | `ai-toolstack/skills/vendor/mattpocock/domain-modeling/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `request-refactor-plan` | 216 | `ai-toolstack/skills/vendor/mattpocock/request-refactor-plan/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `design-an-interface` | 214 | `ai-toolstack/skills/vendor/mattpocock/design-an-interface/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `add-api-endpoint` | 185 | `ai-toolstack/skills/thinkingsoc/add-api-endpoint/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `persian-chat-reply` | 174 | `ai-toolstack/cursor-agent-config/global-skills/persian-chat-reply/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `migrate-to-shoehorn` | 168 | `ai-toolstack/skills/vendor/mattpocock/migrate-to-shoehorn/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `diagnosing-bugs` | 156 | `ai-toolstack/skills/vendor/mattpocock/diagnosing-bugs/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `grilling` | 155 | `ai-toolstack/skills/vendor/mattpocock/grilling/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `tdd` | 149 | `ai-toolstack/skills/vendor/mattpocock/tdd/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `use-mcp-toolstack` | 120 | `ai-toolstack/skills/thinkingsoc/use-mcp-toolstack/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `review-thinkingSOC` | 88 | `ai-toolstack/skills/thinkingsoc/review-thinkingSOC/SKILL.md` | add `disable-model-invocation: true` if you only `/` invoke |
| `resolving-merge-conflicts` | 72 | `ai-toolstack/skills/vendor/mattpocock/resolving-merge-conflicts/SKILL.md` | short; keep if auto-match helps |

## User-only (already trimmed)

- `ponytail-debt` — `ai-toolstack/skills/thinkingsoc/ponytail-debt/SKILL.md`
- `ask-matt` — `ai-toolstack/skills/vendor/mattpocock/ask-matt/SKILL.md`
- `decision-mapping` — `ai-toolstack/skills/vendor/mattpocock/decision-mapping/SKILL.md`
- `edit-article` — `ai-toolstack/skills/vendor/mattpocock/edit-article/SKILL.md`
- `git-guardrails-claude-code` — `ai-toolstack/skills/vendor/mattpocock/git-guardrails-claude-code/SKILL.md`
- `grill-me` — `ai-toolstack/skills/vendor/mattpocock/grill-me/SKILL.md`
- `grill-with-docs` — `ai-toolstack/skills/vendor/mattpocock/grill-with-docs/SKILL.md`
- `handoff` — `ai-toolstack/skills/vendor/mattpocock/handoff/SKILL.md`
- `implement` — `ai-toolstack/skills/vendor/mattpocock/implement/SKILL.md`
- `improve-codebase-architecture` — `ai-toolstack/skills/vendor/mattpocock/improve-codebase-architecture/SKILL.md`
- `loop-me` — `ai-toolstack/skills/vendor/mattpocock/loop-me/SKILL.md`
- `obsidian-vault` — `ai-toolstack/skills/vendor/mattpocock/obsidian-vault/SKILL.md`
- `prototype` — `ai-toolstack/skills/vendor/mattpocock/prototype/SKILL.md`
- `scaffold-exercises` — `ai-toolstack/skills/vendor/mattpocock/scaffold-exercises/SKILL.md`
- `setup-matt-pocock-skills` — `ai-toolstack/skills/vendor/mattpocock/setup-matt-pocock-skills/SKILL.md`
- … and 14 more
