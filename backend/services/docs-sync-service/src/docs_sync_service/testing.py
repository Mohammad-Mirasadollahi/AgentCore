from __future__ import annotations

from copy import deepcopy
from typing import Any

from .core import (
    CodeSymbol,
    ConflictError,
    DocAnchor,
    Document,
    DocumentationDraft,
    DriftFinding,
    NotFoundError,
    Scope,
    digest,
)


class InMemoryStore:
    """Deterministic Store fake for unit and transport-contract tests."""

    def __init__(self) -> None:
        self._symbols: dict[str, CodeSymbol] = {}
        self._documents: dict[str, Document] = {}
        self._anchors: dict[str, DocAnchor] = {}
        self._findings: dict[str, DriftFinding] = {}
        self._drafts: dict[str, DocumentationDraft] = {}
        self._idempotency: dict[tuple[str, str, str], tuple[str, str]] = {}
        self._events: list[dict[str, Any]] = []

    @staticmethod
    def _scope_key(scope: Scope) -> str:
        return "|".join((scope.tenant_id, scope.workspace_id, scope.project_id, scope.project_group_id or ""))

    @staticmethod
    def _same_project(left: Scope, right: Scope) -> bool:
        return (left.tenant_id, left.workspace_id, left.project_id) == (right.tenant_id, right.workspace_id, right.project_id)

    def get_symbol(self, symbol_id: str, scope: Scope) -> CodeSymbol:
        item = self._symbols.get(symbol_id)
        if item is None or not self._same_project(item.scope, scope):
            raise NotFoundError("symbol not found in project scope")
        return deepcopy(item)

    def find_symbol(self, scope: Scope, repo: str, file_path: str, symbol_path: str) -> CodeSymbol | None:
        for item in self._symbols.values():
            if (
                self._same_project(item.scope, scope)
                and item.repo == repo
                and item.file_path == file_path
                and item.symbol_path == symbol_path
            ):
                return deepcopy(item)
        return None

    def put_symbol(self, symbol: CodeSymbol) -> None:
        self._symbols[symbol.id] = deepcopy(symbol)

    def list_symbols(self, scope: Scope) -> list[CodeSymbol]:
        items = [item for item in self._symbols.values() if self._same_project(item.scope, scope)]
        return deepcopy(sorted(items, key=lambda item: (item.created_at, item.id)))

    def get_document(self, document_id: str, scope: Scope) -> Document:
        item = self._documents.get(document_id)
        if item is None or not self._same_project(item.scope, scope):
            raise NotFoundError("document not found in project scope")
        return deepcopy(item)

    def put_document(self, document: Document) -> None:
        self._documents[document.id] = deepcopy(document)

    def list_documents(self, scope: Scope) -> list[Document]:
        items = [item for item in self._documents.values() if self._same_project(item.scope, scope)]
        return deepcopy(sorted(items, key=lambda item: (item.created_at, item.id)))

    def get_anchor(self, anchor_id: str, scope: Scope) -> DocAnchor:
        item = self._anchors.get(anchor_id)
        if item is None or not self._same_project(item.scope, scope):
            raise NotFoundError("anchor not found in project scope")
        return deepcopy(item)

    def put_anchor(self, anchor: DocAnchor) -> None:
        self._anchors[anchor.id] = deepcopy(anchor)

    def list_anchors(self, scope: Scope, symbol_id: str | None = None) -> list[DocAnchor]:
        items = [item for item in self._anchors.values() if self._same_project(item.scope, scope)]
        if symbol_id is not None:
            items = [item for item in items if item.symbol_id == symbol_id]
        return deepcopy(sorted(items, key=lambda item: (item.created_at, item.id)))

    def get_finding(self, finding_id: str, scope: Scope) -> DriftFinding:
        item = self._findings.get(finding_id)
        if item is None or not self._same_project(item.scope, scope):
            raise NotFoundError("drift finding not found in project scope")
        return deepcopy(item)

    def put_finding(self, finding: DriftFinding) -> None:
        self._findings[finding.id] = deepcopy(finding)

    def list_findings(self, scope: Scope) -> list[DriftFinding]:
        items = [item for item in self._findings.values() if self._same_project(item.scope, scope)]
        return deepcopy(sorted(items, key=lambda item: (item.created_at, item.id)))

    def get_draft(self, draft_id: str, scope: Scope) -> DocumentationDraft:
        item = self._drafts.get(draft_id)
        if item is None or not self._same_project(item.scope, scope):
            raise NotFoundError("documentation draft not found in project scope")
        return deepcopy(item)

    def put_draft(self, draft: DocumentationDraft) -> None:
        self._drafts[draft.id] = deepcopy(draft)

    def list_drafts(self, scope: Scope) -> list[DocumentationDraft]:
        items = [item for item in self._drafts.values() if self._same_project(item.scope, scope)]
        return deepcopy(sorted(items, key=lambda item: (item.created_at, item.id)))

    def idempotent(self, scope: Scope, command: str, key: str, payload: dict[str, Any]) -> str | None:
        remembered = self._idempotency.get((self._scope_key(scope), command, key))
        if remembered is None:
            return None
        fingerprint, record_id = remembered
        if fingerprint != digest(payload):
            raise ConflictError("idempotency key was reused with a different payload")
        return record_id

    def remember(self, scope: Scope, command: str, key: str, payload: dict[str, Any], record_id: str) -> None:
        self._idempotency[(self._scope_key(scope), command, key)] = (digest(payload), record_id)

    def event(self, payload: dict[str, Any]) -> None:
        self._events.append(deepcopy(payload))

    def outbox(self) -> list[dict[str, Any]]:
        return deepcopy(sorted(self._events, key=lambda event: (event["occurred_at"], event["event_id"])))
