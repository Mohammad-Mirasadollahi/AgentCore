from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .core import ConflictError, NotFoundError, Scope


class InMemoryStore:
    def __init__(self) -> None:
        self._batches: dict[str, dict[str, Any]] = {}
        self._assignments: dict[str, dict[str, Any]] = {}
        self._idempotency: dict[tuple[str, str, str], str] = {}
        self._outbox: list[dict[str, Any]] = []

    @staticmethod
    def _scope_key(scope: Scope) -> str:
        return "|".join((scope.tenant_id, scope.workspace_id, scope.project_id))

    @staticmethod
    def _same(scope: Scope, item: dict[str, Any]) -> bool:
        return (item["tenant_id"], item["workspace_id"], item["project_id"]) == (
            scope.tenant_id,
            scope.workspace_id,
            scope.project_id,
        )

    def begin_idempotency(self, scope: Scope, key: str, resource: str) -> str | None:
        return self._idempotency.get((self._scope_key(scope), key, resource))

    def complete_idempotency(self, scope: Scope, key: str, resource: str, resource_id: str) -> None:
        packed = (self._scope_key(scope), key, resource)
        if packed in self._idempotency and self._idempotency[packed] != resource_id:
            raise ConflictError("idempotency key already bound to another resource")
        self._idempotency[packed] = resource_id

    def append_event(self, event: dict[str, Any]) -> None:
        self._outbox.append(deepcopy(event))

    def outbox(self) -> list[dict[str, Any]]:
        return deepcopy(self._outbox)

    def put_batch(self, batch: dict[str, Any]) -> None:
        self._batches[batch["id"]] = deepcopy(batch)

    def get_batch(self, batch_id: str, scope: Scope) -> dict[str, Any]:
        item = self._batches.get(batch_id)
        if item is None or not self._same(scope, item):
            raise NotFoundError("work batch not found")
        return deepcopy(item)

    def put_assignment(self, assignment: dict[str, Any]) -> None:
        self._assignments[assignment["id"]] = deepcopy(assignment)

    def get_assignment(self, assignment_id: str, scope: Scope) -> dict[str, Any]:
        item = self._assignments.get(assignment_id)
        if item is None or not self._same(scope, item):
            raise NotFoundError("assignment not found")
        return deepcopy(item)

    def list_assignments(self, scope: Scope, batch_id: str | None = None) -> list[dict[str, Any]]:
        items = [a for a in self._assignments.values() if self._same(scope, a)]
        if batch_id:
            items = [a for a in items if a.get("batch_id") == batch_id]
        return deepcopy(sorted(items, key=lambda a: a["id"]))


class DictStore(InMemoryStore):
    """Durable JSON-file store when Postgres is unavailable in local tests."""

    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = Path(path)
        if self._path.exists():
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._batches = raw.get("batches", {})
            self._assignments = raw.get("assignments", {})
            self._idempotency = {tuple(k.split("\x1f")): v for k, v in raw.get("idempotency", {}).items()}
            self._outbox = raw.get("outbox", [])

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "batches": self._batches,
            "assignments": self._assignments,
            "idempotency": {"\x1f".join(k): v for k, v in self._idempotency.items()},
            "outbox": self._outbox,
        }
        self._path.write_text(json.dumps(payload), encoding="utf-8")

    def complete_idempotency(self, scope: Scope, key: str, resource: str, resource_id: str) -> None:
        super().complete_idempotency(scope, key, resource, resource_id)
        self._persist()

    def append_event(self, event: dict[str, Any]) -> None:
        super().append_event(event)
        self._persist()

    def put_batch(self, batch: dict[str, Any]) -> None:
        super().put_batch(batch)
        self._persist()

    def put_assignment(self, assignment: dict[str, Any]) -> None:
        super().put_assignment(assignment)
        self._persist()
