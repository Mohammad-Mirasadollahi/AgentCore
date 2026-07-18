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
    language: str = "python"


class SemanticSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int = Field(default=5, ge=1, le=50)


class GenerationContextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed_symbol_id: str
    max_symbols: int = Field(default=12, ge=1, le=50)


class ValidateGeneratedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str


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
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return service.structural_query(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            symbol_id,
            rel_type,
        )

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

    @api.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "code-graph-service"}

    return api
