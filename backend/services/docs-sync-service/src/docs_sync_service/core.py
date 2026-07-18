from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
import re
from typing import Any, Protocol
from uuid import uuid4


class DocumentState(StrEnum):
    INDEXED = "indexed"
    VALID = "valid"
    INVALID_FRONTMATTER = "invalid_frontmatter"
    STALE = "stale"
    MISSING_ANCHOR = "missing_anchor"
    ARCHIVED = "archived"


class DriftType(StrEnum):
    MISSING_DOC = "missing_doc"
    STALE_DOC = "stale_doc"


class DriftState(StrEnum):
    DETECTED = "detected"
    TRIAGED = "triaged"
    TASK_CREATED = "task_created"
    FIXED = "fixed"
    IGNORED = "ignored"


class DraftState(StrEnum):
    GENERATED = "generated"
    WAITING_FOR_REVIEW = "waiting_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocsSyncError(Exception):
    def __init__(self, code: str, category: str, message: str):
        super().__init__(message)
        self.code, self.category, self.message = code, category, message


class ValidationError(DocsSyncError):
    def __init__(self, message: str):
        super().__init__("validation_error", "validation_error", message)


class ConflictError(DocsSyncError):
    def __init__(self, message: str):
        super().__init__("conflict_error", "conflict_error", message)


class NotFoundError(DocsSyncError):
    def __init__(self, message: str):
        super().__init__("not_found", "not_found_error", message)


REQUIRED_FRONTMATTER = ("doc_id", "title", "owner", "status", "schema_version", "linked_symbols", "decision_refs")
CRITICAL_TAGS = {"auth", "authorization", "security", "billing", "pricing"}
HIGH_TAGS = {"api", "route", "schema", "contract", "migration", "public"}


@dataclass(frozen=True)
class Scope:
    tenant_id: str
    workspace_id: str
    project_id: str
    project_group_id: str | None = None

    def __post_init__(self) -> None:
        if not all((self.tenant_id.strip(), self.workspace_id.strip(), self.project_id.strip())):
            raise ValidationError("tenant_id, workspace_id, and project_id are required")


@dataclass
class CodeSymbol:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    repo: str
    file_path: str
    symbol_path: str
    kind: str
    signature_hash: str
    body_hash: str
    doc_required: bool
    tags: list[str]
    created_at: str
    updated_at: str
    version: int = 1

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "repo": self.repo,
            "file_path": self.file_path,
            "symbol_path": self.symbol_path,
            "kind": self.kind,
            "signature_hash": self.signature_hash,
            "body_hash": self.body_hash,
            "doc_required": self.doc_required,
            "tags": self.tags,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Document:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    path: str
    title: str
    owner: str
    state: DocumentState
    schema_version: str
    linked_symbols: list[str]
    decision_refs: list[str]
    frontmatter: dict[str, Any]
    body: str
    created_at: str
    updated_at: str
    version: int = 1

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "path": self.path,
            "title": self.title,
            "owner": self.owner,
            "state": self.state.value,
            "schema_version": self.schema_version,
            "linked_symbols": self.linked_symbols,
            "decision_refs": self.decision_refs,
            "frontmatter": self.frontmatter,
            "body": self.body,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class DocAnchor:
    id: str
    scope: Scope
    doc_id: str
    symbol_id: str
    recorded_hash: str
    status: str
    created_at: str
    updated_at: str
    version: int = 1

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "doc_id": self.doc_id,
            "symbol_id": self.symbol_id,
            "recorded_hash": self.recorded_hash,
            "status": self.status,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class DriftFinding:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    symbol_id: str
    doc_id: str | None
    drift_type: DriftType
    old_hash: str | None
    new_hash: str
    severity: Severity
    status: DriftState
    issue_ref: str
    task_ref: str | None
    evidence_refs: list[str]
    created_at: str
    updated_at: str
    version: int = 1

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "symbol_id": self.symbol_id,
            "doc_id": self.doc_id,
            "drift_type": self.drift_type.value,
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
            "severity": self.severity.value,
            "status": self.status.value,
            "issue_ref": self.issue_ref,
            "task_ref": self.task_ref,
            "evidence_refs": self.evidence_refs,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class DocumentationDraft:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    symbol_id: str
    finding_id: str | None
    title: str
    body: str
    state: DraftState
    created_at: str
    updated_at: str
    version: int = 1

    def approve(self, at: str) -> None:
        if self.state not in {DraftState.GENERATED, DraftState.WAITING_FOR_REVIEW}:
            raise ConflictError("draft is not approvable")
        self.state = DraftState.APPROVED
        self.version += 1
        self.updated_at = at

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "symbol_id": self.symbol_id,
            "finding_id": self.finding_id,
            "title": self.title,
            "body": self.body,
            "state": self.state.value,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class BloomFilter:
    """Deterministic membership filter for documented symbol ids."""

    def __init__(self, size: int = 2048, hashes: int = 3, version: str = "1"):
        self.size = size
        self.hashes = hashes
        self.version = version
        self._bits = bytearray(size)

    def add(self, value: str) -> None:
        for index in self._indexes(value):
            self._bits[index] = 1

    def might_contain(self, value: str) -> bool:
        return all(self._bits[index] for index in self._indexes(value))

    def _indexes(self, value: str) -> list[int]:
        digest_value = sha256(value.encode()).hexdigest()
        return [int(digest_value[i * 8 : (i + 1) * 8], 16) % self.size for i in range(self.hashes)]


class Store(Protocol):
    def get_symbol(self, symbol_id: str, scope: Scope) -> CodeSymbol: ...
    def find_symbol(self, scope: Scope, repo: str, file_path: str, symbol_path: str) -> CodeSymbol | None: ...
    def put_symbol(self, symbol: CodeSymbol) -> None: ...
    def list_symbols(self, scope: Scope) -> list[CodeSymbol]: ...
    def get_document(self, document_id: str, scope: Scope) -> Document: ...
    def put_document(self, document: Document) -> None: ...
    def list_documents(self, scope: Scope) -> list[Document]: ...
    def get_anchor(self, anchor_id: str, scope: Scope) -> DocAnchor: ...
    def put_anchor(self, anchor: DocAnchor) -> None: ...
    def list_anchors(self, scope: Scope, symbol_id: str | None = None) -> list[DocAnchor]: ...
    def get_finding(self, finding_id: str, scope: Scope) -> DriftFinding: ...
    def put_finding(self, finding: DriftFinding) -> None: ...
    def list_findings(self, scope: Scope) -> list[DriftFinding]: ...
    def get_draft(self, draft_id: str, scope: Scope) -> DocumentationDraft: ...
    def put_draft(self, draft: DocumentationDraft) -> None: ...
    def list_drafts(self, scope: Scope) -> list[DocumentationDraft]: ...
    def idempotent(self, scope: Scope, command: str, key: str, payload: dict[str, Any]) -> str | None: ...
    def remember(self, scope: Scope, command: str, key: str, payload: dict[str, Any], record_id: str) -> None: ...
    def event(self, payload: dict[str, Any]) -> None: ...
    def outbox(self) -> list[dict[str, Any]]: ...


class DocsSyncService:
    def __init__(self, store: Store):
        self.store = store
        self._bloom: dict[str, BloomFilter] = {}

    def index_symbol(self, scope: Scope, actor: str, correlation_id: str, key: str, payload: dict[str, Any]) -> CodeSymbol:
        self._require_key(key)
        payload = sanitize(payload)
        missing = [field for field in ("repo", "file_path", "symbol_path", "kind", "body") if not payload.get(field)]
        if missing:
            raise ValidationError("missing required fields: " + ", ".join(missing))
        normalized_body = normalize_source(payload["body"])
        signature = payload.get("signature") or payload["symbol_path"]
        command_payload = {
            "repo": payload["repo"],
            "file_path": payload["file_path"],
            "symbol_path": payload["symbol_path"],
            "kind": payload["kind"],
            "signature": signature,
            "body": normalized_body,
            "doc_required": bool(payload.get("doc_required", True)),
            "tags": sorted(set(payload.get("tags") or [])),
        }
        prior = self.store.idempotent(scope, "index_symbol", key, command_payload)
        if prior:
            return self.store.get_symbol(prior, scope)
        timestamp = now()
        existing = self.store.find_symbol(
            scope, command_payload["repo"], command_payload["file_path"], command_payload["symbol_path"]
        )
        if existing:
            existing.kind = command_payload["kind"]
            existing.signature_hash = digest(signature)
            existing.body_hash = digest(normalized_body)
            existing.doc_required = command_payload["doc_required"]
            existing.tags = command_payload["tags"]
            existing.version += 1
            existing.updated_at = timestamp
            existing.actor_id = actor
            existing.correlation_id = correlation_id
            symbol = existing
        else:
            symbol = CodeSymbol(
                str(uuid4()),
                scope,
                actor,
                correlation_id,
                command_payload["repo"],
                command_payload["file_path"],
                command_payload["symbol_path"],
                command_payload["kind"],
                digest(signature),
                digest(normalized_body),
                command_payload["doc_required"],
                command_payload["tags"],
                timestamp,
                timestamp,
            )
        self.store.put_symbol(symbol)
        self.store.remember(scope, "index_symbol", key, command_payload, symbol.id)
        self.emit("SymbolIndexed", symbol.public(), scope, actor, correlation_id, key, symbol.id, [])
        return symbol

    def validate_frontmatter(self, frontmatter: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not isinstance(frontmatter, dict):
            return ["frontmatter must be an object"]
        for field_name in REQUIRED_FRONTMATTER:
            if field_name not in frontmatter:
                errors.append(f"missing required field: {field_name}")
        if "linked_symbols" in frontmatter and not isinstance(frontmatter["linked_symbols"], list):
            errors.append("linked_symbols must be a list")
        if "decision_refs" in frontmatter and not isinstance(frontmatter["decision_refs"], list):
            errors.append("decision_refs must be a list")
        if frontmatter.get("owner") is not None and not str(frontmatter.get("owner") or "").strip():
            errors.append("owner must be non-empty")
        if frontmatter.get("status") not in {None, "draft", "active", "deprecated", "archived"}:
            errors.append("invalid status")
        return errors

    def index_document(self, scope: Scope, actor: str, correlation_id: str, key: str, payload: dict[str, Any]) -> Document:
        self._require_key(key)
        payload = sanitize(payload)
        if not payload.get("path"):
            raise ValidationError("path is required")
        frontmatter = payload.get("frontmatter") or {}
        errors = self.validate_frontmatter(frontmatter)
        if errors:
            raise ValidationError("frontmatter validation failed: " + "; ".join(errors))
        command_payload = {
            "path": payload["path"],
            "frontmatter": frontmatter,
            "body": payload.get("body") or "",
        }
        prior = self.store.idempotent(scope, "index_document", key, command_payload)
        if prior:
            return self.store.get_document(prior, scope)
        timestamp = now()
        document = Document(
            str(frontmatter.get("doc_id") or uuid4()),
            scope,
            actor,
            correlation_id,
            command_payload["path"],
            str(frontmatter["title"]),
            str(frontmatter["owner"]),
            DocumentState.VALID,
            str(frontmatter["schema_version"]),
            list(frontmatter.get("linked_symbols") or []),
            list(frontmatter.get("decision_refs") or []),
            dict(frontmatter),
            command_payload["body"],
            timestamp,
            timestamp,
        )
        self.store.put_document(document)
        self.store.remember(scope, "index_document", key, command_payload, document.id)
        self.emit("DocumentIndexed", document.public(), scope, actor, correlation_id, key, document.id, [])
        return document

    def register_anchor(self, scope: Scope, actor: str, correlation_id: str, key: str, payload: dict[str, Any]) -> DocAnchor:
        self._require_key(key)
        payload = sanitize(payload)
        missing = [field for field in ("doc_id", "symbol_id", "recorded_hash") if not payload.get(field)]
        if missing:
            raise ValidationError("missing required fields: " + ", ".join(missing))
        document = self.store.get_document(payload["doc_id"], scope)
        if document.state == DocumentState.INVALID_FRONTMATTER:
            raise ConflictError("cannot anchor an invalid document")
        symbol = self.store.get_symbol(payload["symbol_id"], scope)
        command_payload = {
            "doc_id": payload["doc_id"],
            "symbol_id": payload["symbol_id"],
            "recorded_hash": payload["recorded_hash"],
        }
        prior = self.store.idempotent(scope, "register_anchor", key, command_payload)
        if prior:
            return self.store.get_anchor(prior, scope)
        timestamp = now()
        status = "synced" if payload["recorded_hash"] == symbol.body_hash else "stale"
        anchor = DocAnchor(
            str(uuid4()),
            scope,
            payload["doc_id"],
            payload["symbol_id"],
            payload["recorded_hash"],
            status,
            timestamp,
            timestamp,
        )
        self.store.put_anchor(anchor)
        self.store.remember(scope, "register_anchor", key, command_payload, anchor.id)
        self._rebuild_bloom(scope)
        self.emit("AnchorRegistered", anchor.public(), scope, actor, correlation_id, key, anchor.id, [])
        self.emit("DocCoverageChanged", self.get_doc_coverage(scope), scope, actor, correlation_id, key, anchor.id, [])
        return anchor

    def detect_drift(self, scope: Scope, actor: str, correlation_id: str, key: str, symbol_ids: list[str] | None = None) -> list[DriftFinding]:
        self._require_key(key)
        payload = {"symbol_ids": sorted(symbol_ids or [])}
        prior = self.store.idempotent(scope, "detect_drift", key, payload)
        if prior:
            return [self.store.get_finding(item_id, scope) for item_id in prior.split(",") if item_id]
        symbols = self.store.list_symbols(scope)
        if symbol_ids:
            wanted = set(symbol_ids)
            symbols = [symbol for symbol in symbols if symbol.id in wanted]
        findings: list[DriftFinding] = []
        timestamp = now()
        for symbol in symbols:
            anchors = self.store.list_anchors(scope, symbol.id)
            if symbol.doc_required and not anchors:
                findings.append(self._create_finding(scope, actor, correlation_id, symbol, None, DriftType.MISSING_DOC, None, symbol.body_hash, timestamp))
                continue
            for anchor in anchors:
                if anchor.recorded_hash != symbol.body_hash:
                    anchor.status = "stale"
                    anchor.version += 1
                    anchor.updated_at = timestamp
                    self.store.put_anchor(anchor)
                    findings.append(
                        self._create_finding(
                            scope,
                            actor,
                            correlation_id,
                            symbol,
                            anchor.doc_id,
                            DriftType.STALE_DOC,
                            anchor.recorded_hash,
                            symbol.body_hash,
                            timestamp,
                        )
                    )
                else:
                    anchor.status = "synced"
                    self.store.put_anchor(anchor)
        if not findings:
            self.store.remember(scope, "detect_drift", key, payload, "")
            return []
        joined = ",".join(finding.id for finding in findings)
        self.store.remember(scope, "detect_drift", key, payload, joined)
        return findings

    def create_draft(self, scope: Scope, actor: str, correlation_id: str, key: str, payload: dict[str, Any]) -> DocumentationDraft:
        self._require_key(key)
        payload = sanitize(payload)
        if not payload.get("symbol_id") or not payload.get("title") or not payload.get("body"):
            raise ValidationError("symbol_id, title, and body are required")
        self.store.get_symbol(payload["symbol_id"], scope)
        command_payload = {
            "symbol_id": payload["symbol_id"],
            "title": payload["title"],
            "body": payload["body"],
            "finding_id": payload.get("finding_id"),
        }
        prior = self.store.idempotent(scope, "create_draft", key, command_payload)
        if prior:
            return self.store.get_draft(prior, scope)
        timestamp = now()
        draft = DocumentationDraft(
            str(uuid4()),
            scope,
            actor,
            correlation_id,
            command_payload["symbol_id"],
            command_payload.get("finding_id"),
            command_payload["title"],
            command_payload["body"],
            DraftState.WAITING_FOR_REVIEW,
            timestamp,
            timestamp,
        )
        self.store.put_draft(draft)
        self.store.remember(scope, "create_draft", key, command_payload, draft.id)
        self.emit("DocumentationDraftCreated", draft.public(), scope, actor, correlation_id, key, draft.id, [])
        return draft

    def approve_draft(self, scope: Scope, actor: str, correlation_id: str, key: str, draft_id: str) -> DocumentationDraft:
        self._require_key(key)
        payload = {"draft_id": draft_id}
        prior = self.store.idempotent(scope, "approve_draft", key, payload)
        if prior:
            return self.store.get_draft(prior, scope)
        draft = self.store.get_draft(draft_id, scope)
        draft.approve(now())
        self.store.put_draft(draft)
        self.store.remember(scope, "approve_draft", key, payload, draft.id)
        self.emit("DocumentationDraftApproved", draft.public(), scope, actor, correlation_id, key, draft.id, [])
        return draft

    def find_docs_for_symbol(self, scope: Scope, symbol_id: str) -> list[Document]:
        self.store.get_symbol(symbol_id, scope)
        doc_ids = {anchor.doc_id for anchor in self.store.list_anchors(scope, symbol_id)}
        return [document for document in self.store.list_documents(scope) if document.id in doc_ids]

    def list_drift_findings(self, scope: Scope) -> list[DriftFinding]:
        return self.store.list_findings(scope)

    def get_doc_coverage(self, scope: Scope) -> dict[str, Any]:
        symbols = self.store.list_symbols(scope)
        entries = []
        documented = 0
        required = 0
        for symbol in symbols:
            has_doc = bool(self.store.list_anchors(scope, symbol.id))
            if symbol.doc_required:
                required += 1
            if has_doc:
                documented += 1
            entries.append(
                {
                    "symbol_id": symbol.id,
                    "symbol_path": symbol.symbol_path,
                    "doc_required": symbol.doc_required,
                    "has_doc": has_doc,
                    "lookup_source": "graph",
                }
            )
        return {
            "required_symbols": required,
            "documented_symbols": documented,
            "coverage_ratio": round(documented / required, 3) if required else 1.0,
            "entries": entries,
        }

    def explain_doc_impact(self, scope: Scope, symbol_id: str) -> dict[str, Any]:
        symbol = self.store.get_symbol(symbol_id, scope)
        anchors = self.store.list_anchors(scope, symbol_id)
        findings = [finding for finding in self.store.list_findings(scope) if finding.symbol_id == symbol_id]
        return {
            "symbol": symbol.public(),
            "severity": severity_for(symbol).value,
            "anchors": [anchor.public() for anchor in anchors],
            "findings": [finding.public() for finding in findings],
            "bloom_maybe_documented": self.bloom_lookup(scope, symbol_id)["maybe_documented"],
        }

    def find_missing_docs(self, scope: Scope) -> list[dict[str, Any]]:
        missing = []
        for symbol in self.store.list_symbols(scope):
            if symbol.doc_required and not self.store.list_anchors(scope, symbol.id):
                missing.append({"symbol": symbol.public(), "severity": severity_for(symbol).value})
        return missing

    def bloom_lookup(self, scope: Scope, symbol_id: str) -> dict[str, Any]:
        bloom = self._bloom_for(scope)
        maybe = bloom.might_contain(symbol_id)
        verified = bool(self.store.list_anchors(scope, symbol_id)) if maybe else False
        return {
            "symbol_id": symbol_id,
            "filter_version": bloom.version,
            "maybe_documented": maybe,
            "verified_has_doc": verified if maybe else False,
            "definite_no_doc": not maybe,
        }

    def evaluate_ci_gate(self, scope: Scope, waived_finding_ids: list[str] | None = None) -> dict[str, Any]:
        waived = set(waived_finding_ids or [])
        findings = [finding for finding in self.store.list_findings(scope) if finding.status != DriftState.FIXED]
        blockers = []
        warnings = []
        for finding in findings:
            if finding.id in waived:
                continue
            if finding.severity == Severity.CRITICAL:
                blockers.append(finding.public())
            elif finding.severity == Severity.HIGH:
                blockers.append(finding.public())
            elif finding.severity == Severity.MEDIUM:
                warnings.append(finding.public())
        decision = "fail" if blockers else "pass"
        return {
            "decision": decision,
            "blockers": blockers,
            "warnings": warnings,
            "waived_finding_ids": sorted(waived),
        }

    def _create_finding(
        self,
        scope: Scope,
        actor: str,
        correlation_id: str,
        symbol: CodeSymbol,
        doc_id: str | None,
        drift_type: DriftType,
        old_hash: str | None,
        new_hash: str,
        timestamp: str,
    ) -> DriftFinding:
        severity = severity_for(symbol)
        finding_id = str(uuid4())
        actionable = severity in {Severity.HIGH, Severity.CRITICAL} or drift_type == DriftType.MISSING_DOC
        finding = DriftFinding(
            finding_id,
            scope,
            actor,
            correlation_id,
            symbol.id,
            doc_id,
            drift_type,
            old_hash,
            new_hash,
            severity,
            DriftState.TASK_CREATED if actionable else DriftState.DETECTED,
            f"issue:{finding_id}",
            f"task:docs-agent:{finding_id}" if actionable else None,
            [symbol.id] + ([doc_id] if doc_id else []),
            timestamp,
            timestamp,
        )
        self.store.put_finding(finding)
        self.emit("DocumentationDriftDetected", finding.public(), scope, actor, correlation_id, "", finding.id, finding.evidence_refs)
        return finding

    def _rebuild_bloom(self, scope: Scope) -> BloomFilter:
        bloom = BloomFilter(version=digest(scope.project_id + now())[:12])
        for anchor in self.store.list_anchors(scope):
            bloom.add(anchor.symbol_id)
        self._bloom[self._scope_key(scope)] = bloom
        return bloom

    def _bloom_for(self, scope: Scope) -> BloomFilter:
        key = self._scope_key(scope)
        if key not in self._bloom:
            return self._rebuild_bloom(scope)
        return self._bloom[key]

    @staticmethod
    def _scope_key(scope: Scope) -> str:
        return "|".join((scope.tenant_id, scope.workspace_id, scope.project_id))

    def _require_key(self, key: str) -> None:
        if not key:
            raise ValidationError("Idempotency-Key header is required")

    def emit(self, event_type: str, payload: dict[str, Any], scope: Scope, actor: str, correlation_id: str, key: str, causation_id: str, evidence_refs: list[str]) -> None:
        self.store.event(
            {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "event_version": 1,
                "occurred_at": now(),
                "producer": "docs-sync-service",
                "tenant_id": scope.tenant_id,
                "workspace_id": scope.workspace_id,
                "project_id": scope.project_id,
                "project_group_id": scope.project_group_id,
                "actor_ref": actor,
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "idempotency_key": key,
                "payload": payload,
                "evidence_refs": evidence_refs,
            }
        )


def severity_for(symbol: CodeSymbol) -> Severity:
    tags = {tag.lower() for tag in symbol.tags} | {symbol.kind.lower()}
    if tags & CRITICAL_TAGS:
        return Severity.CRITICAL
    if tags & HIGH_TAGS:
        return Severity.HIGH
    if not symbol.doc_required:
        return Severity.LOW
    return Severity.MEDIUM


SECRET = re.compile(r"(?i)((?:api[_-]?key|token|password|secret)\s*[:=]\s*)([^\s,;]+)")


def now() -> str:
    return datetime.now(UTC).isoformat()


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return SECRET.sub(r"\1[REDACTED]", value)
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items()}
    return value


def digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256(encoded).hexdigest()


def normalize_source(value: str) -> str:
    """Drop formatting noise while preserving control-flow tokens."""
    without_block = re.sub(r"/\*.*?\*/", "", value, flags=re.S)
    without_line = re.sub(r"#.*$|//.*$", "", without_block, flags=re.M)
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+|[(){}\[\].,=:<>!&|+*/%-]", without_line)
    return " ".join(tokens)
