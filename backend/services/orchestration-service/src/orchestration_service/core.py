from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4


class OrchestrationError(Exception):
    def __init__(self, code: str, category: str, message: str):
        super().__init__(message)
        self.code, self.category, self.message = code, category, message


class ValidationError(OrchestrationError):
    def __init__(self, message: str):
        super().__init__("validation_error", "validation_error", message)


class ConflictError(OrchestrationError):
    def __init__(self, message: str):
        super().__init__("conflict_error", "conflict_error", message)


class NotFoundError(OrchestrationError):
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
    def put_batch(self, batch: dict[str, Any]) -> None: ...
    def get_batch(self, batch_id: str, scope: Scope) -> dict[str, Any]: ...
    def put_assignment(self, assignment: dict[str, Any]) -> None: ...
    def get_assignment(self, assignment_id: str, scope: Scope) -> dict[str, Any]: ...
    def list_assignments(self, scope: Scope, batch_id: str | None = None) -> list[dict[str, Any]]: ...


class OrchestrationService:
    def __init__(self, store: Store):
        self.store = store

    def open_work_batch(
        self,
        scope: Scope,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValidationError("title is required")
        existing = self.store.begin_idempotency(scope, idempotency_key, "work_batch")
        if existing:
            return self.store.get_batch(existing, scope)
        batch_id = _new_id("wb")
        batch = {
            "id": batch_id,
            "tenant_id": scope.tenant_id,
            "workspace_id": scope.workspace_id,
            "project_id": scope.project_id,
            "title": title,
            "status": "open",
            "opened_by": actor_id,
            "correlation_id": correlation_id,
            "task_ids": [str(t) for t in (payload.get("task_ids") or [])],
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.put_batch(batch)
        self.store.complete_idempotency(scope, idempotency_key, "work_batch", batch_id)
        self.store.append_event({"event_type": "work_batch.opened", "batch_id": batch_id})
        return batch

    def route_task(
        self,
        scope: Scope,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        task_id = str(payload.get("task_id") or "").strip()
        agent_type = str(payload.get("agent_type") or "").strip()
        batch_id = str(payload.get("batch_id") or "").strip() or None
        if not task_id or not agent_type:
            raise ValidationError("task_id and agent_type are required")
        if batch_id:
            batch = self.store.get_batch(batch_id, scope)
            if batch["status"] not in {"open", "routing"}:
                raise ConflictError("work batch is not open for routing")
        existing = self.store.begin_idempotency(scope, idempotency_key, "assignment")
        if existing:
            return self.store.get_assignment(existing, scope)
        assignment_id = _new_id("asg")
        assignment = {
            "id": assignment_id,
            "tenant_id": scope.tenant_id,
            "workspace_id": scope.workspace_id,
            "project_id": scope.project_id,
            "task_id": task_id,
            "agent_type": agent_type,
            "batch_id": batch_id,
            "status": "assigned",
            "routed_by": actor_id,
            "correlation_id": correlation_id,
            "created_at": _now(),
        }
        self.store.put_assignment(assignment)
        if batch_id:
            batch = self.store.get_batch(batch_id, scope)
            batch["status"] = "routing"
            batch["updated_at"] = _now()
            if task_id not in batch["task_ids"]:
                batch["task_ids"].append(task_id)
            self.store.put_batch(batch)
        self.store.complete_idempotency(scope, idempotency_key, "assignment", assignment_id)
        self.store.append_event({"event_type": "task.routed", "assignment_id": assignment_id})
        return assignment

    def close_work_batch(self, scope: Scope, batch_id: str) -> dict[str, Any]:
        batch = self.store.get_batch(batch_id, scope)
        if batch["status"] == "closed":
            return batch
        batch["status"] = "closed"
        batch["updated_at"] = _now()
        self.store.put_batch(batch)
        self.store.append_event({"event_type": "work_batch.closed", "batch_id": batch_id})
        return batch

    def complete_assignment(self, scope: Scope, assignment_id: str, actor_id: str) -> dict[str, Any]:
        assignment = self.store.get_assignment(assignment_id, scope)
        if assignment["status"] == "completed":
            return assignment
        if assignment["status"] != "assigned":
            raise ConflictError("assignment cannot be completed from current status")
        assignment["status"] = "completed"
        assignment["completed_by"] = actor_id
        assignment["completed_at"] = _now()
        self.store.put_assignment(assignment)
        self.store.append_event({"event_type": "assignment.completed", "assignment_id": assignment_id})
        return assignment

    def list_assignments(self, scope: Scope, batch_id: str | None = None) -> list[dict[str, Any]]:
        return self.store.list_assignments(scope, batch_id=batch_id)
