from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4


class CommonContextError(Exception):
    def __init__(self, code: str, category: str, message: str):
        super().__init__(message)
        self.code, self.category, self.message = code, category, message


class ValidationError(CommonContextError):
    def __init__(self, message: str):
        super().__init__("validation_error", "validation_error", message)


class ConflictError(CommonContextError):
    def __init__(self, message: str):
        super().__init__("conflict_error", "conflict_error", message)


class NotFoundError(CommonContextError):
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
    def put_item(self, item: dict[str, Any]) -> None: ...
    def get_item(self, item_id: str, scope: Scope) -> dict[str, Any]: ...
    def list_items(self, scope: Scope, status: str | None = None) -> list[dict[str, Any]]: ...


class CommonContextService:
    def __init__(self, store: Store):
        self.store = store

    def propose_item(
        self,
        scope: Scope,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        title = str(payload.get("title") or "").strip()
        body = str(payload.get("body") or "").strip()
        if not title or not body:
            raise ValidationError("title and body are required")
        existing = self.store.begin_idempotency(scope, idempotency_key, "common_item")
        if existing:
            return self.store.get_item(existing, scope)
        item_id = _new_id("cci")
        scores = {
            "frequency": float(payload.get("frequency") or 1.0),
            "recency": float(payload.get("recency") or 1.0),
            "confidence": float(payload.get("confidence") or 0.5),
            "user_pinning": float(payload.get("user_pinning") or 0.0),
            "task_similarity": float(payload.get("task_similarity") or 0.5),
            "project_relevance": float(payload.get("project_relevance") or 0.5),
            "effectiveness": float(payload.get("effectiveness") or 0.5),
        }
        score = (
            scores["frequency"] * 0.2
            + scores["recency"] * 0.15
            + scores["confidence"] * 0.2
            + scores["user_pinning"] * 0.15
            + scores["task_similarity"] * 0.1
            + scores["project_relevance"] * 0.1
            + scores["effectiveness"] * 0.1
        )
        item = {
            "id": item_id,
            "tenant_id": scope.tenant_id,
            "workspace_id": scope.workspace_id,
            "project_id": scope.project_id,
            "title": title,
            "body": body,
            "status": "proposed",
            "score": score,
            "score_components": scores,
            "workflow_type": payload.get("workflow_type"),
            "task_type": payload.get("task_type"),
            "created_by": actor_id,
            "correlation_id": correlation_id,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.put_item(item)
        self.store.complete_idempotency(scope, idempotency_key, "common_item", item_id)
        self.store.append_event({"event_type": "common_item.proposed", "item_id": item_id})
        return item

    def approve_item(self, scope: Scope, item_id: str, actor_id: str) -> dict[str, Any]:
        item = self.store.get_item(item_id, scope)
        if item["status"] == "approved":
            return item
        if item["status"] not in {"proposed", "under_review"}:
            raise ConflictError("item cannot be approved from current status")
        item["status"] = "approved"
        item["approved_by"] = actor_id
        item["updated_at"] = _now()
        self.store.put_item(item)
        self.store.append_event({"event_type": "common_item.approved", "item_id": item_id})
        return item

    def suppress_item(self, scope: Scope, item_id: str, actor_id: str, reason: str = "") -> dict[str, Any]:
        item = self.store.get_item(item_id, scope)
        if item["status"] == "suppressed":
            return item
        if item["status"] in {"archived", "deprecated"}:
            raise ConflictError("item cannot be suppressed from current status")
        item["status"] = "suppressed"
        item["suppressed_by"] = actor_id
        item["suppress_reason"] = reason.strip()
        item["updated_at"] = _now()
        self.store.put_item(item)
        self.store.append_event(
            {"event_type": "common_item.suppressed", "item_id": item_id, "reason": item["suppress_reason"]}
        )
        return item

    def reject_item(self, scope: Scope, item_id: str, actor_id: str, reason: str = "") -> dict[str, Any]:
        item = self.store.get_item(item_id, scope)
        if item["status"] == "rejected":
            return item
        if item["status"] not in {"proposed", "under_review"}:
            raise ConflictError("item cannot be rejected from current status")
        item["status"] = "rejected"
        item["rejected_by"] = actor_id
        item["reject_reason"] = reason.strip()
        item["updated_at"] = _now()
        self.store.put_item(item)
        self.store.append_event(
            {"event_type": "common_item.rejected", "item_id": item_id, "reason": item["reject_reason"]}
        )
        return item

    def resolve_bundle(self, scope: Scope, token_budget: int = 800) -> dict[str, Any]:
        if token_budget < 1:
            raise ValidationError("token_budget must be >= 1")
        approved = [i for i in self.store.list_items(scope, status="approved")]
        approved.sort(key=lambda i: i["score"], reverse=True)
        included: list[dict[str, Any]] = []
        used = 0
        for item in approved:
            cost = max(20, len(item["body"]) // 4)
            if used + cost > token_budget:
                continue
            included.append({"id": item["id"], "title": item["title"], "body": item["body"], "score": item["score"]})
            used += cost
        return {
            "project_id": scope.project_id,
            "token_budget": token_budget,
            "tokens_used": used,
            "included": included,
            "omitted_count": max(0, len(approved) - len(included)),
            "selection_reason": "score_desc_within_token_budget",
        }
