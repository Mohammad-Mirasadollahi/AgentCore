from typing import Any
from uuid import uuid4

from fastapi import Body, FastAPI, Header, Request
from fastapi.responses import JSONResponse

from .bootstrap import build_service
from .core import CommonContextError, CommonContextService, Scope


def app(service: CommonContextService | None = None) -> FastAPI:
    service = service or build_service()
    api = FastAPI(title="AgentCore Common Context API", version="1.0.0")

    @api.exception_handler(CommonContextError)
    async def domain_error(_: Request, exc: CommonContextError):
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
                    "documentation_ref": "backend/services/common-context-service/docs/phase-common-context-api-contract.md",
                }
            },
            status_code=status_code,
        )

    @api.post("/api/v1/projects/{project_id}/common-items")
    async def propose_item(
        project_id: str,
        body: dict[str, Any],
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        x_correlation_id: str | None = Header(default=None),
        idempotency_key: str = Header(alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        item = service.propose_item(
            Scope(x_tenant_id, x_workspace_id, project_id),
            x_actor_id,
            x_correlation_id or str(uuid4()),
            idempotency_key,
            body,
        )
        return {"item": item}

    @api.post("/api/v1/projects/{project_id}/common-items/{item_id}:approve")
    async def approve_item(
        project_id: str,
        item_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        item = service.approve_item(Scope(x_tenant_id, x_workspace_id, project_id), item_id, x_actor_id)
        return {"item": item}

    @api.post("/api/v1/projects/{project_id}/common-items/{item_id}:suppress")
    async def suppress_item(
        project_id: str,
        item_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        body: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        reason = str(body.get("reason") or "")
        item = service.suppress_item(Scope(x_tenant_id, x_workspace_id, project_id), item_id, x_actor_id, reason)
        return {"item": item}

    @api.post("/api/v1/projects/{project_id}/common-items/{item_id}:reject")
    async def reject_item(
        project_id: str,
        item_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        body: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        reason = str(body.get("reason") or "")
        item = service.reject_item(Scope(x_tenant_id, x_workspace_id, project_id), item_id, x_actor_id, reason)
        return {"item": item}

    @api.get("/api/v1/projects/{project_id}/common-context/bundle")
    async def resolve_bundle(
        project_id: str,
        token_budget: int = 800,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        _ = x_actor_id
        bundle = service.resolve_bundle(Scope(x_tenant_id, x_workspace_id, project_id), token_budget)
        return {"bundle": bundle}

    return api
