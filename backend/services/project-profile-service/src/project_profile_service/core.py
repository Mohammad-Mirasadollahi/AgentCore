from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4


class ProjectProfileError(Exception):
    def __init__(self, code: str, category: str, message: str):
        super().__init__(message)
        self.code, self.category, self.message = code, category, message


class ValidationError(ProjectProfileError):
    def __init__(self, message: str):
        super().__init__("validation_error", "validation_error", message)


class ConflictError(ProjectProfileError):
    def __init__(self, message: str):
        super().__init__("conflict_error", "conflict_error", message)


class NotFoundError(ProjectProfileError):
    def __init__(self, message: str):
        super().__init__("not_found", "not_found_error", message)


@dataclass(frozen=True)
class Scope:
    tenant_id: str
    workspace_id: str
    project_id: str

    def __post_init__(self) -> None:
        if not all((self.tenant_id.strip(), self.workspace_id.strip(), self.project_id.strip())):
            raise ValidationError("tenant_id, workspace_id, and project_id are required")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"

class Store(Protocol):
    def begin_idempotency(self, scope: Scope, key: str, resource: str) -> str | None: ...
    def complete_idempotency(self, scope: Scope, key: str, resource: str, resource_id: str) -> None: ...
    def append_event(self, event: dict[str, Any]) -> None: ...
    def put_project(self, project: dict[str, Any]) -> None: ...
    def get_project(self, project_id: str, scope: Scope) -> dict[str, Any]: ...
    def put_group(self, group: dict[str, Any]) -> None: ...
    def get_group(self, group_id: str, tenant_id: str, workspace_id: str) -> dict[str, Any]: ...


class ProjectProfileService:
    def __init__(self, store: Store):
        self.store = store

    def register_project(
        self,
        scope: Scope,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        name = str(payload.get("name") or "").strip()
        domain_pack = str(payload.get("domain_pack") or "default").strip()
        feature_profile = str(payload.get("feature_profile") or "default").strip()
        if not name:
            raise ValidationError("name is required")
        existing = self.store.begin_idempotency(scope, idempotency_key, "project")
        if existing:
            return self.store.get_project(existing, scope)
        project = {
            "id": scope.project_id,
            "tenant_id": scope.tenant_id,
            "workspace_id": scope.workspace_id,
            "project_id": scope.project_id,
            "name": name,
            "domain_pack": domain_pack,
            "feature_profile": feature_profile,
            "project_group_id": payload.get("project_group_id"),
            "isolation": "strict",
            "created_by": actor_id,
            "correlation_id": correlation_id,
            "created_at": _now(),
            "status": "active",
        }
        self.store.put_project(project)
        self.store.complete_idempotency(scope, idempotency_key, "project", scope.project_id)
        self.store.append_event({"event_type": "project.registered", "project_id": scope.project_id})
        return project

    def create_project_group(
        self,
        tenant_id: str,
        workspace_id: str,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        name = str(payload.get("name") or "").strip()
        if not name or not tenant_id.strip() or not workspace_id.strip():
            raise ValidationError("name, tenant_id, and workspace_id are required")
        scope = Scope(tenant_id, workspace_id, "_groups")
        existing = self.store.begin_idempotency(scope, idempotency_key, "project_group")
        if existing:
            return self.store.get_group(existing, tenant_id, workspace_id)
        group_id = _new_id("pg")
        group = {
            "id": group_id,
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "name": name,
            "share_policy": str(payload.get("share_policy") or "explicit_opt_in"),
            "member_project_ids": [str(p) for p in (payload.get("member_project_ids") or [])],
            "created_by": actor_id,
            "correlation_id": correlation_id,
            "created_at": _now(),
        }
        self.store.put_group(group)
        self.store.complete_idempotency(scope, idempotency_key, "project_group", group_id)
        self.store.append_event({"event_type": "project_group.created", "group_id": group_id})
        return group

    def get_project(self, scope: Scope) -> dict[str, Any]:
        return self.store.get_project(scope.project_id, scope)

    def update_feature_profile(
        self,
        scope: Scope,
        actor_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        project = self.store.get_project(scope.project_id, scope)
        domain_pack = payload.get("domain_pack")
        feature_profile = payload.get("feature_profile")
        if domain_pack is None and feature_profile is None:
            raise ValidationError("domain_pack or feature_profile is required")
        if domain_pack is not None:
            value = str(domain_pack).strip()
            if not value:
                raise ValidationError("domain_pack cannot be empty")
            project["domain_pack"] = value
        if feature_profile is not None:
            value = str(feature_profile).strip()
            if not value:
                raise ValidationError("feature_profile cannot be empty")
            project["feature_profile"] = value
        project["updated_by"] = actor_id
        project["updated_at"] = _now()
        self.store.put_project(project)
        self.store.append_event(
            {
                "event_type": "project.profile_updated",
                "project_id": scope.project_id,
                "domain_pack": project["domain_pack"],
                "feature_profile": project["feature_profile"],
            }
        )
        return project
