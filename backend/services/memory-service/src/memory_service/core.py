from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
import re
from typing import Any, Protocol
from uuid import uuid4


class MemoryKind(StrEnum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    RESTRICTED = "restricted"
    DEPRECATED = "deprecated"


class MemoryState(StrEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    STALE = "stale"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class QuestionState(StrEnum):
    OBSERVED = "observed"
    SEARCHING = "searching"
    ANSWERED = "answered"
    DRAFT_GENERATED = "draft_generated"
    APPROVED_FAQ = "approved_faq"
    BLOCKED_BY_GAP = "blocked_by_gap"


class BatchState(StrEnum):
    OPEN = "open"
    ACTIVE = "active"
    READY = "ready_for_consolidation"
    CONSOLIDATING = "consolidating"
    COMPLETED = "completed"


class MemoryError(Exception):
    def __init__(self, code: str, category: str, message: str):
        super().__init__(message)
        self.code = code
        self.category = category
        self.message = message


class ValidationError(MemoryError):
    def __init__(self, message: str):
        super().__init__("validation_error", "validation_error", message)


class ConflictError(MemoryError):
    def __init__(self, message: str):
        super().__init__("conflict_error", "conflict_error", message)


class NotFoundError(MemoryError):
    def __init__(self, message: str):
        super().__init__("not_found", "not_found_error", message)


@dataclass(frozen=True)
class Scope:
    tenant_id: str
    workspace_id: str
    project_id: str
    project_group_id: str | None = None

    def __post_init__(self) -> None:
        if not all((self.tenant_id.strip(), self.workspace_id.strip(), self.project_id.strip())):
            raise ValidationError("tenant_id, workspace_id, and project_id are required")


@dataclass(frozen=True)
class WeightProfile:
    profile_id: str
    version: int
    semantic_weight: float
    episodic_weight: float
    working_weight: float
    evidence_weight: float
    recency_weight: float
    min_relevance_score: float
    faq_min_observations: int
    faq_min_evidence: int
    context_token_budget: int

    curiosity_min_observations: int = 2
    documentation_draft_min_confidence: float = 0.75
    documentation_task_min_confidence: float = 0.4
    current_state_boost: float = 2.0
    episodic_penalty: float = 1.5

    @classmethod
    def from_catalog(cls, data: dict[str, Any]) -> WeightProfile:
        weights = data.get("feature_weights") or {}
        thresholds = data.get("thresholds") or {}
        return cls(
            profile_id=str(data.get("profile_id") or "default-memory-profile"),
            version=int(data.get("version") or 1),
            semantic_weight=float(weights.get("semantic_weight", 3.0)),
            episodic_weight=float(weights.get("episodic_weight", 1.0)),
            working_weight=float(weights.get("working_weight", 2.0)),
            evidence_weight=float(weights.get("evidence_weight", 1.5)),
            recency_weight=float(weights.get("recency_weight", 0.25)),
            min_relevance_score=float(thresholds.get("min_relevance_score", 2.0)),
            faq_min_observations=int(thresholds.get("faq_min_observations", 2)),
            faq_min_evidence=int(thresholds.get("faq_min_evidence", 1)),
            context_token_budget=int(thresholds.get("context_token_budget", 1200)),
            curiosity_min_observations=int(thresholds.get("curiosity_min_observations", 2)),
            documentation_draft_min_confidence=float(
                thresholds.get("documentation_draft_min_confidence", 0.75)
            ),
            documentation_task_min_confidence=float(
                thresholds.get("documentation_task_min_confidence", 0.4)
            ),
            current_state_boost=float(weights.get("current_state_boost", 2.0)),
            episodic_penalty=float(weights.get("episodic_penalty", 1.5)),
        )

    @classmethod
    def default(cls) -> WeightProfile:
        try:
            from weight_profiles import get_active_profile_id, load_profile

            return cls.from_catalog(load_profile(get_active_profile_id()))
        except Exception:  # noqa: BLE001 — keep hardcoded baseline if catalog missing
            return cls(
                profile_id="default-memory-profile",
                version=1,
                semantic_weight=3.0,
                episodic_weight=1.0,
                working_weight=2.0,
                evidence_weight=1.5,
                recency_weight=0.25,
                min_relevance_score=2.0,
                faq_min_observations=2,
                faq_min_evidence=1,
                context_token_budget=1200,
                curiosity_min_observations=2,
                documentation_draft_min_confidence=0.75,
                documentation_task_min_confidence=0.4,
                current_state_boost=2.0,
                episodic_penalty=1.5,
            )


@dataclass
class MemoryItem:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    kind: MemoryKind
    state: MemoryState
    title: str
    body: str
    tags: list[str]
    evidence_refs: list[str]
    source_refs: list[str]
    confidence: float
    created_at: str
    updated_at: str
    version: int = 1

    def activate(self, at: str) -> None:
        if self.state not in {MemoryState.CANDIDATE, MemoryState.STALE}:
            raise ConflictError("only candidate or stale memory can be activated")
        self.state = MemoryState.ACTIVE
        self.updated_at = at
        self.version += 1

    def mark_stale(self, at: str, reason: str) -> None:
        if self.state not in {MemoryState.ACTIVE, MemoryState.CANDIDATE}:
            raise ConflictError("only active or candidate memory can become stale")
        self.state = MemoryState.STALE
        self.updated_at = at
        self.version += 1
        self.tags = sorted(set([*self.tags, "stale:" + slug(reason)]))

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "project_group_id": self.scope.project_group_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "kind": self.kind.value,
            "state": self.state.value,
            "title": self.title,
            "body": self.body,
            "tags": self.tags,
            "evidence_refs": self.evidence_refs,
            "source_refs": self.source_refs,
            "confidence": self.confidence,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class QuestionMemory:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    normalized_question: str
    observations: int
    evidence_refs: list[str]
    state: QuestionState
    answer: str | None
    created_at: str
    updated_at: str
    version: int = 1

    def observe(self, evidence_refs: list[str], at: str) -> None:
        self.observations += 1
        self.evidence_refs = sorted(set([*self.evidence_refs, *evidence_refs]))
        self.updated_at = at
        self.version += 1

    def approve_faq(self, answer: str, profile: WeightProfile, at: str) -> None:
        if self.observations < profile.faq_min_observations or len(self.evidence_refs) < profile.faq_min_evidence:
            raise ConflictError("FAQ promotion requires repeated observations and evidence")
        self.answer = answer
        self.state = QuestionState.APPROVED_FAQ
        self.updated_at = at
        self.version += 1

    def curiosity_score(self) -> float:
        # Linear observation score; replace with a full weighted curiosity profile when needed.
        unresolved = 1.0 if self.state not in {QuestionState.APPROVED_FAQ, QuestionState.DRAFT_GENERATED} else 0.0
        evidence = min(len(self.evidence_refs), 3) * 0.5
        return round(float(self.observations) + unresolved + evidence, 3)

    def resolve_documentation(self, confidence: float, draft_content: str | None, profile: WeightProfile, at: str) -> str:
        if confidence < 0 or confidence > 1:
            raise ValidationError("confidence must be between 0 and 1")
        if confidence >= profile.documentation_draft_min_confidence:
            if not draft_content or not draft_content.strip():
                raise ValidationError("draft_content is required for documentation draft outcomes")
            self.answer = draft_content
            self.state = QuestionState.DRAFT_GENERATED
            outcome = "documentation_draft"
        elif confidence >= profile.documentation_task_min_confidence:
            self.answer = draft_content
            self.state = QuestionState.SEARCHING
            outcome = "task"
        else:
            self.answer = None
            self.state = QuestionState.BLOCKED_BY_GAP
            outcome = "knowledge_gap"
        self.updated_at = at
        self.version += 1
        return outcome

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "normalized_question": self.normalized_question,
            "observations": self.observations,
            "evidence_refs": self.evidence_refs,
            "state": self.state.value,
            "answer": self.answer,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class WorkBatch:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    title: str
    item_refs: list[str]
    deferred_actions: list[str]
    state: BatchState
    created_at: str
    updated_at: str
    version: int = 1

    def mark_ready(self, at: str, reason: str) -> None:
        if self.state not in {BatchState.OPEN, BatchState.ACTIVE}:
            raise ConflictError("only open or active batches can be marked ready")
        if not self.item_refs:
            raise ValidationError("batch requires item_refs before consolidation")
        self.state = BatchState.READY
        self.deferred_actions = sorted(set([*self.deferred_actions, "ready:" + slug(reason)]))
        self.updated_at = at
        self.version += 1

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "title": self.title,
            "item_refs": self.item_refs,
            "deferred_actions": self.deferred_actions,
            "state": self.state.value,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ContextBundle:
    bundle_id: str
    scope: Scope
    query: str
    token_budget: int
    profile: WeightProfile
    items: list[dict[str, Any]]
    excluded: list[dict[str, Any]]
    built_at: str

    def public(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "query": self.query,
            "token_budget": self.token_budget,
            "weight_profile": {"profile_id": self.profile.profile_id, "version": self.profile.version},
            "prompt_cache": {"profile_id": self.profile.profile_id, "version": self.profile.version},
            "items": self.items,
            "excluded": self.excluded,
            "built_at": self.built_at,
        }


class Store(Protocol):
    def get_memory(self, memory_id: str, scope: Scope) -> MemoryItem: ...
    def put_memory(self, item: MemoryItem) -> None: ...
    def list_memory(self, scope: Scope) -> list[MemoryItem]: ...
    def get_question(self, question_id: str, scope: Scope) -> QuestionMemory: ...
    def find_question(self, normalized: str, scope: Scope) -> QuestionMemory | None: ...
    def put_question(self, question: QuestionMemory) -> None: ...
    def list_questions(self, scope: Scope) -> list[QuestionMemory]: ...
    def get_batch(self, batch_id: str, scope: Scope) -> WorkBatch: ...
    def put_batch(self, batch: WorkBatch) -> None: ...
    def list_batches(self, scope: Scope) -> list[WorkBatch]: ...
    def idempotent(self, scope: Scope, command: str, key: str, payload: dict[str, Any]) -> str | None: ...
    def remember(self, scope: Scope, command: str, key: str, payload: dict[str, Any], record_id: str) -> None: ...
    def event(self, payload: dict[str, Any]) -> None: ...
    def outbox(self) -> list[dict[str, Any]]: ...


class MemoryService:
    def __init__(self, store: Store, profile: WeightProfile | None = None):
        self.store = store
        self.profile = profile or WeightProfile.default()

    def create_memory(self, scope: Scope, actor: str, correlation_id: str, key: str, payload: dict[str, Any]) -> MemoryItem:
        self._require_key(key)
        payload = sanitize(payload)
        self._validate_memory_payload(payload)
        prior = self.store.idempotent(scope, "create_memory", key, payload)
        if prior:
            return self.store.get_memory(prior, scope)
        timestamp = now()
        kind = MemoryKind(payload["kind"])
        state = MemoryState.RESTRICTED if kind == MemoryKind.RESTRICTED else MemoryState(payload.get("state") or MemoryState.CANDIDATE.value)
        item = MemoryItem(
            str(uuid4()),
            scope,
            actor,
            correlation_id,
            kind,
            state,
            payload["title"],
            payload["body"],
            sorted(set(payload.get("tags") or [])),
            sorted(set(payload.get("evidence_refs") or [])),
            sorted(set(payload.get("source_refs") or [])),
            float(payload.get("confidence", 1.0)),
            timestamp,
            timestamp,
        )
        self.store.put_memory(item)
        self.store.remember(scope, "create_memory", key, payload, item.id)
        self.emit("MemoryItemCreated", item.public(), scope, actor, correlation_id, key, item.id, item.evidence_refs)
        return item

    def consolidate_memory(self, scope: Scope, actor: str, correlation_id: str, key: str, memory_ids: list[str], reason: str) -> list[MemoryItem]:
        self._require_key(key)
        payload = {"memory_ids": memory_ids, "reason": sanitize(reason)}
        prior = self.store.idempotent(scope, "consolidate_memory", key, payload)
        if prior:
            return [self.store.get_memory(memory_id, scope) for memory_id in prior.split(",") if memory_id]
        if not memory_ids:
            raise ValidationError("memory_ids are required")
        consolidated: list[MemoryItem] = []
        timestamp = now()
        for memory_id in memory_ids:
            item = self.store.get_memory(memory_id, scope)
            if item.kind == MemoryKind.RESTRICTED:
                continue
            item.activate(timestamp)
            item.tags = sorted(set([*item.tags, "consolidated:" + slug(reason)]))
            self.store.put_memory(item)
            consolidated.append(item)
        if not consolidated:
            raise ValidationError("no eligible memory items to consolidate")
        joined = ",".join(item.id for item in consolidated)
        self.store.remember(scope, "consolidate_memory", key, payload, joined)
        self.emit("MemoryConsolidationCompleted", {"memory_ids": [item.id for item in consolidated], "reason": reason}, scope, actor, correlation_id, key, joined, [])
        return consolidated

    def decay_memory(self, scope: Scope, actor: str, correlation_id: str, key: str, memory_ids: list[str], reason: str) -> list[MemoryItem]:
        self._require_key(key)
        payload = {"memory_ids": memory_ids, "reason": sanitize(reason)}
        prior = self.store.idempotent(scope, "decay_memory", key, payload)
        if prior:
            return [self.store.get_memory(memory_id, scope) for memory_id in prior.split(",") if memory_id]
        if not memory_ids:
            raise ValidationError("memory_ids are required")
        decayed: list[MemoryItem] = []
        timestamp = now()
        for memory_id in memory_ids:
            item = self.store.get_memory(memory_id, scope)
            if item.kind == MemoryKind.RESTRICTED:
                continue
            item.mark_stale(timestamp, payload["reason"])
            self.store.put_memory(item)
            decayed.append(item)
        if not decayed:
            raise ValidationError("no eligible memory items to decay")
        joined = ",".join(item.id for item in decayed)
        self.store.remember(scope, "decay_memory", key, payload, joined)
        self.emit("MemoryDecayCompleted", {"memory_ids": [item.id for item in decayed], "reason": reason}, scope, actor, correlation_id, key, joined, [])
        return decayed

    def retrieve_context(self, scope: Scope, actor: str, correlation_id: str, query: str, token_budget: int | None = None) -> ContextBundle:
        if not query.strip():
            raise ValidationError("query is required")
        budget = token_budget or self.profile.context_token_budget
        if budget <= 0:
            raise ValidationError("token_budget must be positive")
        terms = tokenize(query)
        wants_history = bool(terms & HISTORY_TERMS)
        candidates = self.store.list_memory(scope)
        selected: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        used_tokens = 0
        scored = sorted(
            ((self._score(item, terms, wants_history), item) for item in candidates),
            key=lambda pair: (-pair[0], pair[1].created_at, pair[1].id),
        )
        for score, item in scored:
            reason = self._exclude_reason(item, score, wants_history)
            if reason:
                excluded.append({"id": item.id, "reason": reason, "score": round(score, 3)})
                continue
            token_estimate = estimate_tokens(item.title + " " + item.body)
            if used_tokens + token_estimate > budget:
                excluded.append({"id": item.id, "reason": "token_budget_overflow", "score": round(score, 3)})
                continue
            used_tokens += token_estimate
            selected.append(
                {
                    "memory": item.public(),
                    "score": round(score, 3),
                    "selection_reason": "matched query under scoped weight profile",
                    "token_estimate": token_estimate,
                }
            )
        bundle = ContextBundle(str(uuid4()), scope, query, budget, self.profile, selected, excluded, now())
        self.emit("ContextBundleBuilt", bundle.public(), scope, actor, correlation_id, "", bundle.bundle_id, [])
        return bundle

    def explain_retrieval(self, scope: Scope, query: str) -> dict[str, Any]:
        terms = tokenize(query)
        wants_history = bool(terms & HISTORY_TERMS)
        return {
            "query_terms": sorted(terms),
            "wants_history": wants_history,
            "weight_profile": self.profile.__dict__,
            "prompt_cache": {"profile_id": self.profile.profile_id, "version": self.profile.version},
            "candidates": [
                {
                    "id": item.id,
                    "state": item.state.value,
                    "kind": item.kind.value,
                    "score": round(self._score(item, terms, wants_history), 3),
                }
                for item in self.store.list_memory(scope)
            ],
        }

    def observe_question(self, scope: Scope, actor: str, correlation_id: str, key: str, question: str, evidence_refs: list[str]) -> QuestionMemory:
        self._require_key(key)
        normalized = normalize_question(question)
        payload = {"normalized_question": normalized, "evidence_refs": sorted(set(sanitize(evidence_refs)))}
        prior = self.store.idempotent(scope, "observe_question", key, payload)
        if prior:
            return self.store.get_question(prior, scope)
        timestamp = now()
        item = self.store.find_question(normalized, scope)
        if item:
            item.observe(payload["evidence_refs"], timestamp)
        else:
            item = QuestionMemory(str(uuid4()), scope, actor, correlation_id, normalized, 1, payload["evidence_refs"], QuestionState.OBSERVED, None, timestamp, timestamp)
        self.store.put_question(item)
        self.store.remember(scope, "observe_question", key, payload, item.id)
        self.emit("QuestionObserved", item.public(), scope, actor, correlation_id, key, item.id, item.evidence_refs)
        return item

    def promote_faq(self, scope: Scope, actor: str, correlation_id: str, key: str, question_id: str, answer: str) -> QuestionMemory:
        self._require_key(key)
        payload = {"question_id": question_id, "answer": sanitize(answer)}
        prior = self.store.idempotent(scope, "promote_faq", key, payload)
        if prior:
            return self.store.get_question(prior, scope)
        item = self.store.get_question(question_id, scope)
        item.approve_faq(payload["answer"], self.profile, now())
        self.store.put_question(item)
        self.store.remember(scope, "promote_faq", key, payload, item.id)
        self.emit("FAQPromoted", item.public(), scope, actor, correlation_id, key, item.id, item.evidence_refs)
        return item

    def resolve_missing_documentation(
        self,
        scope: Scope,
        actor: str,
        correlation_id: str,
        key: str,
        question_id: str,
        confidence: float,
        draft_content: str | None = None,
    ) -> dict[str, Any]:
        self._require_key(key)
        payload = {
            "question_id": question_id,
            "confidence": confidence,
            "draft_content": sanitize(draft_content) if draft_content is not None else None,
        }
        prior = self.store.idempotent(scope, "resolve_missing_documentation", key, payload)
        if prior:
            item = self.store.get_question(prior, scope)
            return {
                "question_memory": item.public(),
                "outcome": documentation_outcome(item.state),
                "curiosity_score": item.curiosity_score(),
            }
        item = self.store.get_question(question_id, scope)
        outcome = item.resolve_documentation(confidence, payload["draft_content"], self.profile, now())
        self.store.put_question(item)
        self.store.remember(scope, "resolve_missing_documentation", key, payload, item.id)
        event_type = {
            "documentation_draft": "DocumentationDraftCreated",
            "task": "DocumentationTaskSuggested",
            "knowledge_gap": "KnowledgeGapCreated",
        }[outcome]
        result = {
            "question_memory": item.public(),
            "outcome": outcome,
            "curiosity_score": item.curiosity_score(),
        }
        self.emit(event_type, result, scope, actor, correlation_id, key, item.id, item.evidence_refs)
        return result

    def open_batch(self, scope: Scope, actor: str, correlation_id: str, key: str, title: str, item_refs: list[str], deferred_actions: list[str]) -> WorkBatch:
        self._require_key(key)
        if not title.strip():
            raise ValidationError("title is required")
        payload = {"title": sanitize(title), "item_refs": sorted(set(item_refs)), "deferred_actions": sorted(set(deferred_actions))}
        prior = self.store.idempotent(scope, "open_batch", key, payload)
        if prior:
            return self.store.get_batch(prior, scope)
        timestamp = now()
        batch = WorkBatch(str(uuid4()), scope, actor, correlation_id, payload["title"], payload["item_refs"], payload["deferred_actions"], BatchState.OPEN, timestamp, timestamp)
        self.store.put_batch(batch)
        self.store.remember(scope, "open_batch", key, payload, batch.id)
        return batch

    def mark_batch_ready(self, scope: Scope, actor: str, correlation_id: str, key: str, batch_id: str, reason: str) -> WorkBatch:
        self._require_key(key)
        payload = {"batch_id": batch_id, "reason": sanitize(reason)}
        prior = self.store.idempotent(scope, "mark_batch_ready", key, payload)
        if prior:
            return self.store.get_batch(prior, scope)
        batch = self.store.get_batch(batch_id, scope)
        batch.mark_ready(now(), payload["reason"])
        self.store.put_batch(batch)
        self.store.remember(scope, "mark_batch_ready", key, payload, batch.id)
        self.emit("BatchReadyForConsolidation", batch.public(), scope, actor, correlation_id, key, batch.id, batch.item_refs)
        return batch

    def list_repeated_questions(self, scope: Scope) -> list[QuestionMemory]:
        return [item for item in self.store.list_questions(scope) if item.observations >= self.profile.faq_min_observations]

    def list_curious_questions(self, scope: Scope) -> list[dict[str, Any]]:
        curious = []
        for item in self.store.list_questions(scope):
            score = item.curiosity_score()
            if item.observations >= self.profile.curiosity_min_observations and score >= float(self.profile.curiosity_min_observations):
                payload = item.public()
                payload["curiosity_score"] = score
                curious.append(payload)
        return curious

    def list_stale_memory(self, scope: Scope) -> list[MemoryItem]:
        return [item for item in self.store.list_memory(scope) if item.state in {MemoryState.STALE, MemoryState.DEPRECATED}]

    def _score(self, item: MemoryItem, terms: set[str], wants_history: bool = False) -> float:
        haystack = tokenize(" ".join([item.title, item.body, *item.tags]))
        overlap = len(terms & haystack)
        kind_weight = {
            MemoryKind.SEMANTIC: self.profile.semantic_weight,
            MemoryKind.EPISODIC: self.profile.episodic_weight,
            MemoryKind.WORKING: self.profile.working_weight,
            MemoryKind.RESTRICTED: 0.0,
            MemoryKind.DEPRECATED: 0.0,
        }[item.kind]
        evidence = self.profile.evidence_weight if item.evidence_refs else 0.0
        score = (overlap * kind_weight) + evidence + (item.confidence * self.profile.recency_weight)
        if item.state == MemoryState.ACTIVE and item.kind in {MemoryKind.SEMANTIC, MemoryKind.WORKING}:
            score += self.profile.current_state_boost
        if item.kind == MemoryKind.EPISODIC and not wants_history:
            score -= self.profile.episodic_penalty
        if item.state == MemoryState.CANDIDATE:
            score -= 0.5
        return score

    def _exclude_reason(self, item: MemoryItem, score: float, wants_history: bool = False) -> str | None:
        if item.kind == MemoryKind.RESTRICTED or item.state == MemoryState.RESTRICTED:
            return "restricted_memory_boundary"
        if item.state in {MemoryState.DEPRECATED, MemoryState.ARCHIVED}:
            return "inactive_memory_state"
        if item.state == MemoryState.STALE:
            return "stale_memory_excluded"
        if item.kind == MemoryKind.EPISODIC and not wants_history:
            return "historical_fact_not_requested"
        if score < self.profile.min_relevance_score:
            return "below_relevance_threshold"
        return None

    def _validate_memory_payload(self, payload: dict[str, Any]) -> None:
        missing = [field for field in ("kind", "title", "body") if not payload.get(field)]
        if missing:
            raise ValidationError("missing required fields: " + ", ".join(missing))
        try:
            MemoryKind(payload["kind"])
        except ValueError as exc:
            raise ValidationError("invalid memory kind") from exc
        confidence = float(payload.get("confidence", 1.0))
        if confidence < 0 or confidence > 1:
            raise ValidationError("confidence must be between 0 and 1")

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
                "producer": "memory-service",
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


SECRET = re.compile(r"(?i)((?:api[_-]?key|token|password|secret)\s*[:=]\s*)([^\s,;]+)")
HISTORY_TERMS = {"history", "historical", "audit", "past", "previous", "timeline", "root-cause", "migration"}


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


def tokenize(value: str) -> set[str]:
    return {part for part in re.findall(r"[a-z0-9][a-z0-9_-]*", value.lower()) if len(part) > 1}


def normalize_question(value: str) -> str:
    normalized = " ".join(re.findall(r"[a-z0-9][a-z0-9_-]*", value.lower()))
    if not normalized:
        raise ValidationError("question is required")
    return normalized


def slug(value: str) -> str:
    return "-".join(sorted(tokenize(value)))[:80] or "unspecified"


def estimate_tokens(value: str) -> int:
    return max(1, len(value.split()))


def documentation_outcome(state: QuestionState) -> str:
    return {
        QuestionState.DRAFT_GENERATED: "documentation_draft",
        QuestionState.SEARCHING: "task",
        QuestionState.BLOCKED_BY_GAP: "knowledge_gap",
    }.get(state, state.value)
