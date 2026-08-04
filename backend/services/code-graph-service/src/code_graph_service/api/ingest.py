"""Ingest and language-profile HTTP routes."""

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, status

from ..core import CodeGraphService
from .auth import ContentPushHttpAuth
from .common import scope_from
from .schemas import (
    IngestFileRequest,
    IngestPushRequest,
    IngestRepoRequest,
    IngestRuntimeTracesRequest,
    PurgeRequest,
)


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

    @api.post("/api/v1/projects/{project_id}/graph/ingest-push")
    async def ingest_push(
        project_id: str,
        body: IngestPushRequest,
        _auth: ContentPushHttpAuth,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        x_correlation_id: str | None = Header(default=None),
        idempotency_key: str = Header(alias="Idempotency-Key"),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        from code_graph_service.domain.errors import ValidationError
        from code_graph_service.domain.path_safety import safe_repo_rel_path

        scope = scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id)
        dumped = body.model_dump()
        docs = dumped.pop("docs", None)
        result = service.ingest_pushed_sources(
            scope,
            x_actor_id,
            x_correlation_id or str(uuid4()),
            idempotency_key,
            dumped,
        )
        out = result.to_dict()
        if docs is not None:
            upserted = 0
            failed = 0
            errors: list[str] = []
            for entry in docs:
                if not isinstance(entry, dict):
                    failed += 1
                    continue
                try:
                    rel = safe_repo_rel_path(
                        str(entry.get("relative_path") or entry.get("file_path") or "")
                    )
                    doc_id = str(entry.get("doc_id") or "").strip()
                    body_text = entry.get("body")
                    if not isinstance(body_text, str):
                        body_text = "" if body_text is None else str(body_text)
                    if not doc_id:
                        raise ValidationError("doc_id is required")
                    if len(body_text.encode("utf-8", errors="replace")) > 2_000_000:
                        raise ValidationError("doc body exceeds 2_000_000 bytes")
                    tokens = entry.get("linked_symbol_tokens") or []
                    if not isinstance(tokens, list):
                        tokens = []
                    service.upsert_human_documentation(
                        scope,
                        doc_id=doc_id,
                        relative_path=rel,
                        body=body_text,
                        title=str(entry.get("title") or doc_id),
                        linked_symbol_tokens=[str(t) for t in tokens if str(t).strip()],
                    )
                    upserted += 1
                except Exception as exc:  # noqa: BLE001
                    failed += 1
                    errors.append(str(exc)[:200])
            out["docs"] = {
                "docs_upserted": upserted,
                "docs_failed": failed,
                "errors": errors[:20],
            }
        return out

    @api.post("/api/v1/projects/{project_id}/graph/purge")
    async def purge(
        project_id: str,
        body: PurgeRequest,
        _auth: ContentPushHttpAuth,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        if not body.yes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="yes: true is required to confirm destructive purge",
            )
        scope = scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id)
        result = service.purge_scope(scope)
        return {"ok": True, "purge": result}

    @api.get("/api/v1/projects/{project_id}/graph/file-hashes")
    async def file_hashes(
        project_id: str,
        _auth: ContentPushHttpAuth,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        hashes = service.file_content_hashes(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id)
        )
        return {"hashes": hashes}

    @api.post("/api/v1/projects/{project_id}/graph/ingest-runtime-traces")
    async def ingest_runtime_traces(
        project_id: str,
        body: IngestRuntimeTracesRequest,
        x_tenant_id: str = Header(),
        x_workspace_id: str = Header(),
        x_actor_id: str = Header(),
        x_correlation_id: str | None = Header(default=None),
        idempotency_key: str = Header(alias="Idempotency-Key"),
        x_project_group_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return service.ingest_runtime_traces(
            scope_from(project_id, x_tenant_id, x_workspace_id, x_project_group_id),
            x_actor_id,
            x_correlation_id or str(uuid4()),
            idempotency_key,
            body.model_dump(),
        )

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
