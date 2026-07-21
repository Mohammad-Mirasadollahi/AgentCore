# LLM Gateway — internal `graphify_semantic_llm` task

**Scope:** Backend LLM Gateway only. **Graphify enrichment was removed from ai-toolstack (2026-07)** — there is no local enrichment pipeline or MCP Graphify server in this repo anymore.

## What remains in the product

| Piece | Location |
|-------|----------|
| Task type `graphify_semantic_llm` | `backend/services/llm_gateway_service/config_defaults.py` |
| Static-context contract for generate | `backend/lib/thinking_soc_common/llm/graphify_static_context.py` |
| Request validation | `backend/services/llm_gateway_service/schemas.py` |

The task is **hidden from product LLM Settings UI** (internal / legacy API callers only). See [llm-task-type-registration-standard.md](../../backend/docs/standards/llm_gateway_service/llm-task-type-registration-standard.md).

## mTLS to LLM Gateway

On-prem services that call `/internal/generate` with mTLS should use the same trust reconcile patterns as other S2S clients — see [mtls-trust-auto-reconcile.md](../../backend/docs/standards/security/mtls-trust-auto-reconcile.md) (runner supervisor and nginx sync). The former Graphify enrichment hook (`graphify_enrichment.gateway_auth`) is **removed**.

## Agent discovery

Do **not** install Graphify MCP or run enrichment scripts. Use repo docs + narrow `rg` / Read per `ai-toolstack/rules/ai-toolstack.mdc`.
