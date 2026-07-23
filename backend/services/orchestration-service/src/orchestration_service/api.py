from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from .bootstrap import ServiceContainer, build_container
from .core import OrchestrationError, OrchestrationService, Scope


def build_app(
    service: OrchestrationService | None = None,
    *,
    container: ServiceContainer | None = None,
) -> FastAPI:
    """Compose FastAPI with a process-scoped ``ServiceContainer`` on ``app.state``."""
    if container is not None and service is not None and service is not container.service:
        raise ValueError("pass either service or container, not conflicting both")
    if container is None:
        if service is not None:
            container = ServiceContainer(service=service, settings=None)
        else:
            container = build_container()
    service = container.service
    api = FastAPI(title="AgentCore Orchestration API", version="1.0.0")
    api.state.container = container

    @api.exception_handler(OrchestrationError)
    async def domain_error(_: Request, exc: OrchestrationError):
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
                    "documentation_ref": "backend/services/orchestration-service/docs/phase-orchestration-api-contract.md",
                }
            },
            status_code=status_code,
        )

    @api.post("/api/v1/projects/{project_id}/work-batches")
    async def open_batch(
        project_id: str,
        body: dict[str, Any],
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        x_correlation_id: str | None = Header(default=None),
        idempotency_key: str = Header(alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        batch = service.open_work_batch(
            Scope(x_tenant_id, x_workspace_id, project_id),
            x_actor_id,
            x_correlation_id or str(uuid4()),
            idempotency_key,
            body,
        )
        return {"batch": batch}

    @api.post("/api/v1/projects/{project_id}/assignments")
    async def route_task(
        project_id: str,
        body: dict[str, Any],
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        x_correlation_id: str | None = Header(default=None),
        idempotency_key: str = Header(alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        assignment = service.route_task(
            Scope(x_tenant_id, x_workspace_id, project_id),
            x_actor_id,
            x_correlation_id or str(uuid4()),
            idempotency_key,
            body,
        )
        return {"assignment": assignment}

    @api.post("/api/v1/projects/{project_id}/work-batches/{batch_id}:close")
    async def close_batch(
        project_id: str,
        batch_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        _ = x_actor_id
        batch = service.close_work_batch(Scope(x_tenant_id, x_workspace_id, project_id), batch_id)
        return {"batch": batch}

    @api.post("/api/v1/projects/{project_id}/assignments/{assignment_id}:complete")
    async def complete_assignment(
        project_id: str,
        assignment_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        assignment = service.complete_assignment(
            Scope(x_tenant_id, x_workspace_id, project_id),
            assignment_id,
            x_actor_id,
        )
        return {"assignment": assignment}

    @api.get("/api/v1/projects/{project_id}/assignments")
    async def list_assignments(
        project_id: str,
        batch_id: str | None = None,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        _ = x_actor_id
        items = service.list_assignments(Scope(x_tenant_id, x_workspace_id, project_id), batch_id=batch_id)
        return {"items": items}

    return api


# Backward-compatible alias used by tests and callers.
app = build_app
