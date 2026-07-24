"""Ingest and language-profile HTTP routes."""

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header

from ..core import CodeGraphService
from .common import scope_from
from .schemas import IngestFileRequest, IngestRepoRequest


def register(api: FastAPI, service: CodeGraphService) -> None:
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
