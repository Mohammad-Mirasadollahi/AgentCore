from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .bootstrap import build_service
from .core import CodeGraphError, CodeGraphService, Scope


class IngestFileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str
    source: str
    language: str | None = None


class IngestRepoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_path: str
    include_extensions: list[str] | None = None
    exclude_dirs: list[str] | None = None
    max_files: int = Field(default=2000, ge=1, le=20000)
    max_file_bytes: int = Field(default=1_500_000, ge=1024, le=20_000_000)
    include_outcomes: bool = True


class SemanticSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int = Field(default=5, ge=1, le=50)


class ExploreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int = Field(default=12, ge=1, le=40)
    max_depth: int = Field(default=2, ge=1, le=4)
    budget_chars: int | None = Field(default=None, ge=2000, le=100000)


class DetectChangesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    changed_files: list[str] = Field(min_length=1)
    include_flows: bool = True


class ArchitectureOverviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_n: int = Field(default=10, ge=1, le=50)


class SymbolPathRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_id: str
    end_id: str
    max_depth: int = Field(default=12, ge=1, le=30)


class HybridSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int = Field(default=10, ge=1, le=50)


class PendingSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str


class GenerationContextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed_symbol_id: str
    max_symbols: int = Field(default=12, ge=1, le=50)


class ValidateGeneratedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str


class LlmCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str
    system: str = "You are a helpful assistant."
    model: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=128000)
    response_format_json: bool = False
    # None → gateway env (AGENTCORE_LITELLM_REASONING_*); True/False overrides per call.
    reasoning_enabled: bool | None = None
    reasoning_effort: str | None = Field(default=None, max_length=32)


def app(service: CodeGraphService | None = None) -> FastAPI:
    service = service or build_service()
    api = FastAPI(title="AgentCore Code Graph API", version="1.0.0")

    @api.exception_handler(CodeGraphError)
    async def graph_error(_: Request, exc: CodeGraphError):
        status_code = 400 if exc.category == "validation_error" else 409 if exc.category == "conflict_error" else 404
        return JSONResponse(
            {
                "error": {
                    "error_code": exc.code,
                    "category": exc.category,
                    "message": exc.message,
                    "retryable": False,
                    "correlation_id": None,
                    "details": {},
                    "documentation_ref": "docs/07-code-knowledge-graph",
                }
            },
            status_code=status_code,
        )

    def scope_from(
        project_id: str,
        tenant_id: str,
        workspace_id: str,
        project_group_id: str | None = None,
    ) -> Scope:
        return Scope(tenant_id, workspace_id, project_id, project_group_id)

    @api.post("/api/v1/projects/{project_id}/graph/ingest-file")
    async def ingest_file(
        project_id: str,
        body: IngestFileRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        x_correlation_id: str | None = Header(default=None),
        idempotency_key: str = Header(alias="Idempotency-Key"),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        result = service.ingest_file(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            x_actor_id,
            x_correlation_id or str(uuid4()),
            idempotency_key,
            body.model_dump(),
        )
        return {
            "file_id": result.file_id,
            "symbols_indexed": result.symbols_indexed,
            "symbols_changed": result.symbols_changed,
            "symbols_documented": result.symbols_documented,
            "edges_written": result.edges_written,
            "changed_symbol_ids": result.changed_symbol_ids,
        }

    @api.post("/api/v1/projects/{project_id}/graph/ingest-repo")
    async def ingest_repo(
        project_id: str,
        body: IngestRepoRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        x_correlation_id: str | None = Header(default=None),
        idempotency_key: str = Header(alias="Idempotency-Key"),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        result = service.ingest_repo(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            x_actor_id,
            x_correlation_id or str(uuid4()),
            idempotency_key,
            body.model_dump(),
        )
        return result.to_dict()

    @api.get("/api/v1/projects/{project_id}/graph/language-profile")
    async def language_profile(
        project_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        profile = service.get_polyglot_profile(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id)
        )
        return profile.to_dict()

    @api.get("/api/v1/projects/{project_id}/graph/symbols/{symbol_id}")
    async def get_symbol(
        project_id: str,
        symbol_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        symbol = service.get_symbol(scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id), symbol_id)
        return service._symbol_view(symbol)

    @api.get("/api/v1/projects/{project_id}/graph/symbols/{symbol_id}/neighbors")
    async def neighbors(
        project_id: str,
        symbol_id: str,
        rel_type: str | None = None,
        max_depth: int = 1,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return service.structural_query(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            symbol_id,
            rel_type,
            max_depth=max(1, min(max_depth, 5)),
        )

    @api.get("/api/v1/projects/{project_id}/graph/neo4j-capabilities")
    async def neo4j_capabilities(
        project_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        store = service.store
        caps = getattr(store, "capabilities", None)
        if not callable(caps):
            return {"backend": type(store).__name__, "apoc": False, "gds": False, "fulltext": False}
        return {"backend": type(store).__name__, **caps()}

    @api.post("/api/v1/projects/{project_id}/graph/search:semantic")
    async def semantic_search(
        project_id: str,
        body: SemanticSearchRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        hits = service.semantic_search(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            body.query,
            body.top_k,
        )
        return {"hits": hits}

    @api.post("/api/v1/projects/{project_id}/graph/explore")
    async def explore(
        project_id: str,
        body: ExploreRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return service.explore(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            body.query,
            top_k=body.top_k,
            max_depth=body.max_depth,
            budget_chars=body.budget_chars,
        )

    @api.post("/api/v1/projects/{project_id}/graph/detect-changes")
    async def detect_changes(
        project_id: str,
        body: DetectChangesRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return service.detect_changes(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            body.changed_files,
            include_flows=body.include_flows,
        )

    @api.post("/api/v1/projects/{project_id}/graph/architecture-overview")
    async def architecture_overview(
        project_id: str,
        body: ArchitectureOverviewRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return service.architecture_overview(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            top_n=body.top_n,
        )

    @api.post("/api/v1/projects/{project_id}/graph/path")
    async def symbol_path(
        project_id: str,
        body: SymbolPathRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return service.symbol_path(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            body.start_id,
            body.end_id,
            max_depth=body.max_depth,
        )

    @api.post("/api/v1/projects/{project_id}/graph/search:hybrid")
    async def hybrid_search(
        project_id: str,
        body: HybridSearchRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return service.hybrid_search(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            body.query,
            top_k=body.top_k,
        )

    @api.post("/api/v1/projects/{project_id}/graph/pending-sync")
    async def pending_sync(
        project_id: str,
        body: PendingSyncRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _ = scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id)
        return service.mark_file_pending(body.file_path)

    @api.get("/api/v1/projects/{project_id}/graph/freshness")
    async def freshness(
        project_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _ = scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id)
        return service.freshness_status()

    @api.post("/api/v1/projects/{project_id}/graph/generation-context")
    async def generation_context(
        project_id: str,
        body: GenerationContextRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return service.build_generation_context(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            body.seed_symbol_id,
            body.max_symbols,
        )

    @api.post("/api/v1/projects/{project_id}/graph/generated-code:validate")
    async def validate_generated(
        project_id: str,
        body: ValidateGeneratedRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return service.validate_generated_code(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            body.source,
        )

    @api.get("/api/v1/llm/providers")
    async def llm_providers() -> dict[str, Any]:
        """List LiteLLM providers (configured flags from env keys)."""
        providers = service.llm_providers()
        return {
            "providers": providers,
            "configured_count": sum(1 for p in providers if p.get("configured")),
        }

    @api.get("/api/v1/llm/config")
    async def llm_config() -> dict[str, Any]:
        """Public LiteLLM settings (Base URL, timeout, retries — no secrets)."""
        return service.llm_config()

    @api.post("/api/v1/llm/complete")
    async def llm_complete(body: LlmCompleteRequest) -> dict[str, Any]:
        from fastapi import HTTPException

        if service.llm is None:
            raise HTTPException(status_code=503, detail="LLM gateway is not configured on this service")
        from llm_gateway import ChatMessage, CompletionRequest

        try:
            result = service.llm.complete(
                CompletionRequest(
                    messages=(
                        ChatMessage(role="system", content=body.system),
                        ChatMessage(role="user", content=body.prompt),
                    ),
                    model=body.model,
                    temperature=body.temperature,
                    max_tokens=body.max_tokens,
                    response_format_json=body.response_format_json,
                    reasoning_enabled=body.reasoning_enabled,
                    reasoning_effort=body.reasoning_effort,
                )
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {
            "content": result.content,
            "model": result.model,
            "provider": result.provider,
            "usage": result.usage,
        }

    @api.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "code-graph-service"}

    return api
