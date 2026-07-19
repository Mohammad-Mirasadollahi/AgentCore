from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from .bootstrap import build_service
from .core import ProjectProfileError, ProjectProfileService, Scope


def app(service: ProjectProfileService | None = None) -> FastAPI:
    service = service or build_service()
    api = FastAPI(title="AgentCore Project Profile API", version="1.0.0")

    @api.exception_handler(ProjectProfileError)
    async def domain_error(_: Request, exc: ProjectProfileError):
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
                    "documentation_ref": "backend/services/project-profile-service/docs/phase-project-profile-api-contract.md",
                }
            },
            status_code=status_code,
        )

    @api.post("/api/v1/projects/{project_id}/profile")
    async def register_project(
        project_id: str,
        body: dict[str, Any],
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        x_correlation_id: str | None = Header(default=None),
        idempotency_key: str = Header(alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        project = service.register_project(
            Scope(x_tenant_id, x_workspace_id, project_id),
            x_actor_id,
            x_correlation_id or str(uuid4()),
            idempotency_key,
            body,
        )
        return {"project": project}

    @api.get("/api/v1/projects/{project_id}/profile")
    async def get_project(
        project_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        _ = x_actor_id
        project = service.get_project(Scope(x_tenant_id, x_workspace_id, project_id))
        return {"project": project}

    @api.patch("/api/v1/projects/{project_id}/profile")
    async def update_feature_profile(
        project_id: str,
        body: dict[str, Any],
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        project = service.update_feature_profile(
            Scope(x_tenant_id, x_workspace_id, project_id),
            x_actor_id,
            body,
        )
        return {"project": project}

    @api.get("/api/v1/usage-profiles")
    async def list_usage_profiles(
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        _ = (x_tenant_id, x_workspace_id, x_actor_id)
        return {"items": service.list_usage_profiles()}

    @api.post("/api/v1/projects/{project_id}/usage-profile:activate")
    async def activate_usage_profile(
        project_id: str,
        body: dict[str, Any],
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        profile_id = str(body.get("usage_profile") or "").strip()
        project = service.activate_usage_profile(
            Scope(x_tenant_id, x_workspace_id, project_id),
            x_actor_id,
            profile_id,
            apply_catalog_defaults=bool(body.get("apply_catalog_defaults", True)),
        )
        return {"project": project}

    @api.get("/api/v1/projects/{project_id}/usage-profile/effective")
    async def effective_usage_profile(
        project_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        _ = x_actor_id
        effective = service.get_effective_usage_profile(Scope(x_tenant_id, x_workspace_id, project_id))
        return {"effective": effective}

    @api.get("/api/v1/projects/{project_id}/usage-profile/cursor-mcp")
    async def export_cursor_mcp(
        project_id: str,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
    ) -> dict[str, Any]:
        _ = x_actor_id
        return service.export_cursor_mcp_connection(Scope(x_tenant_id, x_workspace_id, project_id))

    @api.post("/api/v1/project-groups")
    async def create_group(
        body: dict[str, Any],
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        x_correlation_id: str | None = Header(default=None),
        idempotency_key: str = Header(alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        group = service.create_project_group(
            x_tenant_id,
            x_workspace_id,
            x_actor_id,
            x_correlation_id or str(uuid4()),
            idempotency_key,
            body,
        )
        return {"group": group}

    return api
