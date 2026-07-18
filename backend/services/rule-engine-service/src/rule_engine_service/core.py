from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
import json
import re
from typing import Any, Protocol
from uuid import uuid4


class RuleState(StrEnum):
    DRAFT = "draft"
    SHADOW = "shadow"
    ACTIVE = "active"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


class EvaluationMode(StrEnum):
    DETERMINISTIC = "deterministic"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    MANUAL = "manual"


class Verdict(StrEnum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    ESCALATE = "escalate"


class EvaluationState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ESCALATED = "escalated"
    ERRORED = "errored"


class ApprovalState(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELED = "canceled"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


SENSITIVE_DOMAINS = {"revenue", "security", "compliance", "production", "auth", "billing"}
TASK_TRIGGERS = {"api", "schema", "contract", "migration", "route"}


class RuleEngineError(Exception):
    def __init__(self, code: str, category: str, message: str):
        super().__init__(message)
        self.code, self.category, self.message = code, category, message


class ValidationError(RuleEngineError):
    def __init__(self, message: str):
        super().__init__("validation_error", "validation_error", message)


class ConflictError(RuleEngineError):
    def __init__(self, message: str):
        super().__init__("conflict_error", "conflict_error", message)


class NotFoundError(RuleEngineError):
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


@dataclass
class Rule:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    title: str
    natural_language_rule: str
    severity: Severity
    owner: str
    evaluation_mode: EvaluationMode
    state: RuleState
    domain: str
    examples: list[str]
    counterexamples: list[str]
    match_tags: list[str]
    required_approval_role: str | None
    precedence: int
    version: int
    created_at: str
    updated_at: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "title": self.title,
            "natural_language_rule": self.natural_language_rule,
            "severity": self.severity.value,
            "owner": self.owner,
            "evaluation_mode": self.evaluation_mode.value,
            "state": self.state.value,
            "domain": self.domain,
            "examples": self.examples,
            "counterexamples": self.counterexamples,
            "match_tags": self.match_tags,
            "required_approval_role": self.required_approval_role,
            "precedence": self.precedence,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RuleEvaluation:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    rule_id: str
    subject_ref: str
    verdict: Verdict
    confidence: float
    rationale: str
    evidence_refs: list[str]
    used_llm: bool
    state: EvaluationState
    shadow: bool
    risk_score: float
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
            "rule_id": self.rule_id,
            "subject_ref": self.subject_ref,
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "evidence_refs": self.evidence_refs,
            "used_llm": self.used_llm,
            "state": self.state.value,
            "shadow": self.shadow,
            "risk_score": self.risk_score,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ApprovalRequest:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    evaluation_id: str
    rule_id: str
    approver: str
    status: ApprovalState
    options: list[str]
    deadline: str
    decision_reason: str | None
    evidence_refs: list[str]
    created_at: str
    updated_at: str
    version: int = 1

    def resolve(self, status: ApprovalState, reason: str, at: str) -> None:
        if self.status != ApprovalState.REQUESTED:
            raise ConflictError("approval is not open")
        if status not in {ApprovalState.APPROVED, ApprovalState.REJECTED, ApprovalState.CANCELED}:
            raise ValidationError("invalid approval resolution")
        self.status = status
        self.decision_reason = reason
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
            "evaluation_id": self.evaluation_id,
            "rule_id": self.rule_id,
            "approver": self.approver,
            "status": self.status.value,
            "options": self.options,
            "deadline": self.deadline,
            "decision_reason": self.decision_reason,
            "evidence_refs": self.evidence_refs,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RoutedTask:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    subject_ref: str
    title: str
    assignee_type: str
    reason: str
    evidence_refs: list[str]
    created_at: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "subject_ref": self.subject_ref,
            "title": self.title,
            "assignee_type": self.assignee_type,
            "reason": self.reason,
            "evidence_refs": self.evidence_refs,
            "created_at": self.created_at,
        }


@dataclass
class AnomalySignal:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    subject_ref: str
    signal_type: str
    score: float
    rationale: str
    evidence_refs: list[str]
    created_at: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "subject_ref": self.subject_ref,
            "signal_type": self.signal_type,
            "score": self.score,
            "rationale": self.rationale,
            "evidence_refs": self.evidence_refs,
            "created_at": self.created_at,
        }


@dataclass
class RuleFeedback:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    evaluation_id: str
    label: str
    note: str
    created_at: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "evaluation_id": self.evaluation_id,
            "label": self.label,
            "note": self.note,
            "created_at": self.created_at,
        }


@dataclass
class ImpactMap:
    id: str
    scope: Scope
    change_ref: str
    affected_entities: list[dict[str, Any]]
    risk_level: Severity
    generated_task_refs: list[str]
    confidence: float
    created_at: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "change_ref": self.change_ref,
            "affected_entities": self.affected_entities,
            "risk_level": self.risk_level.value,
            "generated_task_refs": self.generated_task_refs,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }


@dataclass
class JudgeResult:
    verdict: Verdict
    confidence: float
    rationale: str
    matched_examples: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    recommended_action: str = ""


class Judge(Protocol):
    def judge(self, rule: Rule, subject: dict[str, Any]) -> JudgeResult: ...


class HeuristicJudge:
    """Local semantic judge adapter — no external model calls."""

    def judge(self, rule: Rule, subject: dict[str, Any]) -> JudgeResult:
        haystack = " ".join(
            [
                str(subject.get("summary") or ""),
                " ".join(subject.get("tags") or []),
                " ".join(subject.get("paths") or []),
                str(subject.get("change_type") or ""),
            ]
        ).lower()
        rule_text = (rule.natural_language_rule + " " + " ".join(rule.match_tags)).lower()
        overlap = len(set(tokenize(haystack)) & set(tokenize(rule_text)))
        sensitive = bool(set(subject.get("tags") or []) & SENSITIVE_DOMAINS) or rule.domain in SENSITIVE_DOMAINS
        if sensitive and overlap:
            return JudgeResult(
                Verdict.ESCALATE if rule.severity in {Severity.HIGH, Severity.CRITICAL} else Verdict.BLOCK,
                0.86,
                f"semantic judge matched sensitive policy '{rule.title}' with overlap={overlap}",
                matched_examples=rule.examples[:2],
                recommended_action="request_human_approval",
            )
        if overlap >= 2:
            return JudgeResult(Verdict.WARN, 0.72, f"semantic judge found partial match for '{rule.title}'", rule.examples[:1], [], "warn")
        return JudgeResult(Verdict.ALLOW, 0.9, f"semantic judge found no material conflict with '{rule.title}'", [], [], "allow")


class Store(Protocol):
    def get_rule(self, rule_id: str, scope: Scope) -> Rule: ...
    def put_rule(self, rule: Rule) -> None: ...
    def list_rules(self, scope: Scope) -> list[Rule]: ...
    def get_evaluation(self, evaluation_id: str, scope: Scope) -> RuleEvaluation: ...
    def put_evaluation(self, evaluation: RuleEvaluation) -> None: ...
    def list_evaluations(self, scope: Scope) -> list[RuleEvaluation]: ...
    def get_approval(self, approval_id: str, scope: Scope) -> ApprovalRequest: ...
    def put_approval(self, approval: ApprovalRequest) -> None: ...
    def list_approvals(self, scope: Scope) -> list[ApprovalRequest]: ...
    def put_task(self, task: RoutedTask) -> None: ...
    def list_tasks(self, scope: Scope) -> list[RoutedTask]: ...
    def put_anomaly(self, anomaly: AnomalySignal) -> None: ...
    def list_anomalies(self, scope: Scope) -> list[AnomalySignal]: ...
    def put_feedback(self, feedback: RuleFeedback) -> None: ...
    def list_feedback(self, scope: Scope) -> list[RuleFeedback]: ...
    def put_impact(self, impact: ImpactMap) -> None: ...
    def list_impacts(self, scope: Scope) -> list[ImpactMap]: ...
    def idempotent(self, scope: Scope, command: str, key: str, payload: dict[str, Any]) -> str | None: ...
    def remember(self, scope: Scope, command: str, key: str, payload: dict[str, Any], record_id: str) -> None: ...
    def event(self, payload: dict[str, Any]) -> None: ...
    def outbox(self) -> list[dict[str, Any]]: ...


class RuleEngineService:
    def __init__(self, store: Store, judge: Judge | None = None):
        self.store = store
        self.judge = judge or HeuristicJudge()

    def create_rule(self, scope: Scope, actor: str, correlation_id: str, key: str, payload: dict[str, Any]) -> Rule:
        self._require_key(key)
        payload = sanitize(payload)
        missing = [field for field in ("title", "natural_language_rule", "severity", "owner", "evaluation_mode") if not payload.get(field)]
        if missing:
            raise ValidationError("missing required fields: " + ", ".join(missing))
        try:
            severity = Severity(payload["severity"])
            mode = EvaluationMode(payload["evaluation_mode"])
            state = RuleState(payload.get("state") or RuleState.ACTIVE.value)
        except ValueError as exc:
            raise ValidationError("invalid severity, evaluation_mode, or state") from exc
        command_payload = {
            "title": payload["title"],
            "natural_language_rule": payload["natural_language_rule"],
            "severity": severity.value,
            "owner": payload["owner"],
            "evaluation_mode": mode.value,
            "state": state.value,
            "domain": payload.get("domain") or "engineering",
            "examples": list(payload.get("examples") or []),
            "counterexamples": list(payload.get("counterexamples") or []),
            "match_tags": sorted(set(payload.get("match_tags") or [])),
            "required_approval_role": payload.get("required_approval_role"),
            "precedence": int(payload.get("precedence") or 100),
        }
        prior = self.store.idempotent(scope, "create_rule", key, command_payload)
        if prior:
            return self.store.get_rule(prior, scope)
        timestamp = now()
        rule = Rule(
            str(uuid4()),
            scope,
            actor,
            correlation_id,
            command_payload["title"],
            command_payload["natural_language_rule"],
            severity,
            command_payload["owner"],
            mode,
            state,
            command_payload["domain"],
            command_payload["examples"],
            command_payload["counterexamples"],
            command_payload["match_tags"],
            command_payload["required_approval_role"],
            command_payload["precedence"],
            1,
            timestamp,
            timestamp,
        )
        self.store.put_rule(rule)
        self.store.remember(scope, "create_rule", key, command_payload, rule.id)
        self.emit("RuleCreated", rule.public(), scope, actor, correlation_id, key, rule.id, [])
        return rule

    def update_rule_version(self, scope: Scope, actor: str, correlation_id: str, key: str, rule_id: str, payload: dict[str, Any]) -> Rule:
        self._require_key(key)
        payload = sanitize(payload)
        command_payload = {"rule_id": rule_id, **{k: payload[k] for k in payload}}
        prior = self.store.idempotent(scope, "update_rule_version", key, command_payload)
        if prior:
            return self.store.get_rule(prior, scope)
        rule = self.store.get_rule(rule_id, scope)
        if "natural_language_rule" in payload:
            rule.natural_language_rule = str(payload["natural_language_rule"])
        if "severity" in payload:
            rule.severity = Severity(payload["severity"])
        if "state" in payload:
            rule.state = RuleState(payload["state"])
        if "match_tags" in payload:
            rule.match_tags = sorted(set(payload["match_tags"] or []))
        if "examples" in payload:
            rule.examples = list(payload["examples"] or [])
        if "counterexamples" in payload:
            rule.counterexamples = list(payload["counterexamples"] or [])
        if "evaluation_mode" in payload:
            rule.evaluation_mode = EvaluationMode(payload["evaluation_mode"])
        if "required_approval_role" in payload:
            rule.required_approval_role = payload.get("required_approval_role")
        rule.version += 1
        rule.updated_at = now()
        rule.actor_id = actor
        rule.correlation_id = correlation_id
        self.store.put_rule(rule)
        self.store.remember(scope, "update_rule_version", key, command_payload, rule.id)
        self.emit("RuleUpdated", rule.public(), scope, actor, correlation_id, key, rule.id, [])
        return rule

    def evaluate_rules(self, scope: Scope, actor: str, correlation_id: str, key: str, subject: dict[str, Any], shadow: bool = False) -> dict[str, Any]:
        self._require_key(key)
        subject = sanitize(subject)
        if not subject.get("subject_ref"):
            raise ValidationError("subject_ref is required")
        command_payload = {"subject": subject, "shadow": shadow}
        prior = self.store.idempotent(scope, "evaluate_rules", key, command_payload)
        if prior:
            evaluation_ids = [item for item in prior.split(",") if item]
            evaluations = [self.store.get_evaluation(item_id, scope) for item_id in evaluation_ids]
            return self._replay_evaluation_bundle(scope, subject, evaluations, shadow)

        allowed_states = {RuleState.SHADOW, RuleState.ACTIVE} if shadow else {RuleState.ACTIVE}
        rules = sorted(
            [rule for rule in self.store.list_rules(scope) if rule.state in allowed_states],
            key=lambda item: (-item.precedence, item.created_at, item.id),
        )
        applicable = [rule for rule in rules if self._rule_applies(rule, subject)]
        evaluations: list[RuleEvaluation] = []
        timestamp = now()
        for rule in applicable:
            evaluation = self._evaluate_one(scope, actor, correlation_id, rule, subject, shadow, timestamp)
            self.store.put_evaluation(evaluation)
            evaluations.append(evaluation)
            self.emit("RuleEvaluationCompleted", evaluation.public(), scope, actor, correlation_id, key, evaluation.id, evaluation.evidence_refs)
            if evaluation.verdict in {Verdict.BLOCK, Verdict.ESCALATE} and not shadow:
                self.emit("RuleViolationDetected", evaluation.public(), scope, actor, correlation_id, key, evaluation.id, evaluation.evidence_refs)

        anomalies = self._detect_anomalies(scope, actor, correlation_id, subject, timestamp)
        impact = self._build_impact(scope, subject, timestamp)
        tasks = self._route_tasks(scope, actor, correlation_id, subject, impact, evaluations, timestamp)
        approvals = []
        if not shadow:
            approvals = self._auto_request_approvals(scope, actor, correlation_id, evaluations, timestamp)

        joined = ",".join(item.id for item in evaluations)
        self.store.remember(scope, "evaluate_rules", key, command_payload, joined)
        bundle = self._evaluation_bundle(scope, subject, evaluations, shadow)
        bundle["impact"] = impact.public() if impact else None
        bundle["tasks"] = [task.public() for task in tasks]
        bundle["approvals"] = [item.public() for item in approvals]
        bundle["anomalies"] = [item.public() for item in anomalies]
        return bundle

    def run_shadow(self, scope: Scope, actor: str, correlation_id: str, key: str, subject: dict[str, Any]) -> dict[str, Any]:
        return self.evaluate_rules(scope, actor, correlation_id, key, subject, shadow=True)

    def request_approval(self, scope: Scope, actor: str, correlation_id: str, key: str, evaluation_id: str, approver: str | None = None) -> ApprovalRequest:
        self._require_key(key)
        payload = {"evaluation_id": evaluation_id, "approver": approver}
        prior = self.store.idempotent(scope, "request_approval", key, payload)
        if prior:
            return self.store.get_approval(prior, scope)
        evaluation = self.store.get_evaluation(evaluation_id, scope)
        rule = self.store.get_rule(evaluation.rule_id, scope)
        timestamp = now()
        approval = ApprovalRequest(
            str(uuid4()),
            scope,
            actor,
            correlation_id,
            evaluation.id,
            rule.id,
            approver or rule.required_approval_role or rule.owner,
            ApprovalState.REQUESTED,
            ["approve", "reject", "needs_changes"],
            (datetime.now(UTC) + timedelta(hours=24 if rule.severity != Severity.CRITICAL else 4)).isoformat(),
            None,
            evaluation.evidence_refs,
            timestamp,
            timestamp,
        )
        self.store.put_approval(approval)
        evaluation.state = EvaluationState.ESCALATED
        evaluation.updated_at = timestamp
        self.store.put_evaluation(evaluation)
        self.store.remember(scope, "request_approval", key, payload, approval.id)
        self.emit("ApprovalRequested", approval.public(), scope, actor, correlation_id, key, approval.id, approval.evidence_refs)
        return approval

    def resolve_approval(self, scope: Scope, actor: str, correlation_id: str, key: str, approval_id: str, status: str, reason: str) -> ApprovalRequest:
        self._require_key(key)
        payload = {"approval_id": approval_id, "status": status, "reason": sanitize(reason)}
        prior = self.store.idempotent(scope, "resolve_approval", key, payload)
        if prior:
            return self.store.get_approval(prior, scope)
        approval = self.store.get_approval(approval_id, scope)
        approval.resolve(ApprovalState(status), payload["reason"], now())
        self.store.put_approval(approval)
        self.store.remember(scope, "resolve_approval", key, payload, approval.id)
        self.emit("ApprovalResolved", approval.public(), scope, actor, correlation_id, key, approval.id, approval.evidence_refs)
        return approval

    def route_task(self, scope: Scope, actor: str, correlation_id: str, key: str, payload: dict[str, Any]) -> RoutedTask:
        self._require_key(key)
        payload = sanitize(payload)
        missing = [field for field in ("subject_ref", "title", "assignee_type", "reason") if not payload.get(field)]
        if missing:
            raise ValidationError("missing required fields: " + ", ".join(missing))
        command_payload = {
            "subject_ref": payload["subject_ref"],
            "title": payload["title"],
            "assignee_type": payload["assignee_type"],
            "reason": payload["reason"],
            "evidence_refs": sorted(set(payload.get("evidence_refs") or [])),
        }
        prior = self.store.idempotent(scope, "route_task", key, command_payload)
        if prior:
            return next(task for task in self.store.list_tasks(scope) if task.id == prior)
        for existing in self.store.list_tasks(scope):
            if existing.subject_ref == command_payload["subject_ref"] and existing.assignee_type == command_payload["assignee_type"]:
                self.store.remember(scope, "route_task", key, command_payload, existing.id)
                return existing
        task = RoutedTask(
            str(uuid4()),
            scope,
            actor,
            correlation_id,
            command_payload["subject_ref"],
            command_payload["title"],
            command_payload["assignee_type"],
            command_payload["reason"],
            command_payload["evidence_refs"],
            now(),
        )
        self.store.put_task(task)
        self.store.remember(scope, "route_task", key, command_payload, task.id)
        self.emit("TaskRouted", task.public(), scope, actor, correlation_id, key, task.id, task.evidence_refs)
        return task

    def record_feedback(self, scope: Scope, actor: str, correlation_id: str, key: str, evaluation_id: str, label: str, note: str) -> RuleFeedback:
        self._require_key(key)
        payload = {"evaluation_id": evaluation_id, "label": sanitize(label), "note": sanitize(note)}
        if payload["label"] not in {"false_positive", "true_positive", "needs_tuning"}:
            raise ValidationError("label must be false_positive, true_positive, or needs_tuning")
        prior = self.store.idempotent(scope, "record_feedback", key, payload)
        if prior:
            return next(item for item in self.store.list_feedback(scope) if item.id == prior)
        self.store.get_evaluation(evaluation_id, scope)
        feedback = RuleFeedback(str(uuid4()), scope, actor, correlation_id, evaluation_id, payload["label"], payload["note"], now())
        self.store.put_feedback(feedback)
        self.store.remember(scope, "record_feedback", key, payload, feedback.id)
        self.emit("RuleFeedbackRecorded", feedback.public(), scope, actor, correlation_id, key, feedback.id, [evaluation_id])
        return feedback

    def explain_decision(self, scope: Scope, evaluation_id: str) -> dict[str, Any]:
        evaluation = self.store.get_evaluation(evaluation_id, scope)
        rule = self.store.get_rule(evaluation.rule_id, scope)
        return {
            "evaluation": evaluation.public(),
            "rule": rule.public(),
            "why_applied": evaluation.rationale,
            "used_llm": evaluation.used_llm,
            "evidence_refs": evaluation.evidence_refs,
        }

    def list_evaluations(self, scope: Scope) -> list[RuleEvaluation]:
        return self.store.list_evaluations(scope)

    def get_approval_queue(self, scope: Scope) -> list[ApprovalRequest]:
        return [item for item in self.store.list_approvals(scope) if item.status == ApprovalState.REQUESTED]

    def list_anomalies(self, scope: Scope) -> list[AnomalySignal]:
        return self.store.list_anomalies(scope)

    def get_rule_health(self, scope: Scope) -> dict[str, Any]:
        rules = self.store.list_rules(scope)
        evaluations = self.store.list_evaluations(scope)
        feedback = self.store.list_feedback(scope)
        return {
            "rule_count": len(rules),
            "active_rules": sum(1 for rule in rules if rule.state == RuleState.ACTIVE),
            "shadow_rules": sum(1 for rule in rules if rule.state == RuleState.SHADOW),
            "evaluation_count": len(evaluations),
            "blocked_or_escalated": sum(1 for item in evaluations if item.verdict in {Verdict.BLOCK, Verdict.ESCALATE}),
            "llm_evaluations": sum(1 for item in evaluations if item.used_llm),
            "feedback_count": len(feedback),
            "open_approvals": len(self.get_approval_queue(scope)),
        }

    def _evaluate_one(self, scope: Scope, actor: str, correlation_id: str, rule: Rule, subject: dict[str, Any], shadow: bool, timestamp: str) -> RuleEvaluation:
        evidence = sorted(set((subject.get("evidence_refs") or []) + [subject["subject_ref"], rule.id]))
        used_llm = False
        if rule.evaluation_mode == EvaluationMode.MANUAL:
            verdict, confidence, rationale = Verdict.ESCALATE, 1.0, "manual policy always requires human review"
        elif rule.evaluation_mode == EvaluationMode.DETERMINISTIC:
            verdict, confidence, rationale = self._deterministic(rule, subject)
        elif rule.evaluation_mode == EvaluationMode.HYBRID:
            verdict, confidence, rationale = self._deterministic(rule, subject)
            if verdict == Verdict.ALLOW and self._needs_semantic(rule, subject):
                judged = self.judge.judge(rule, subject)
                used_llm = True
                verdict, confidence, rationale = judged.verdict, judged.confidence, judged.rationale
                evidence = sorted(set(evidence + judged.matched_examples))
        else:
            judged = self.judge.judge(rule, subject)
            used_llm = True
            verdict, confidence, rationale = judged.verdict, judged.confidence, judged.rationale
            evidence = sorted(set(evidence + judged.matched_examples))
            if confidence < 0.7 and rule.severity in {Severity.HIGH, Severity.CRITICAL}:
                verdict, rationale = Verdict.ESCALATE, rationale + "; low-confidence high-risk fallback to escalate"

        if self._is_sensitive(rule, subject) and verdict in {Verdict.BLOCK, Verdict.WARN}:
            verdict = Verdict.ESCALATE
            rationale += "; fail-closed for sensitive domain"

        risk = severity_score(rule.severity)
        if verdict == Verdict.ESCALATE:
            risk = max(risk, 0.9)
        state = {
            Verdict.ALLOW: EvaluationState.PASSED,
            Verdict.WARN: EvaluationState.PASSED,
            Verdict.BLOCK: EvaluationState.FAILED,
            Verdict.ESCALATE: EvaluationState.ESCALATED,
        }[verdict]
        return RuleEvaluation(
            str(uuid4()),
            scope,
            actor,
            correlation_id,
            rule.id,
            subject["subject_ref"],
            verdict,
            confidence,
            rationale,
            evidence,
            used_llm,
            state,
            shadow,
            risk,
            timestamp,
            timestamp,
        )

    def _deterministic(self, rule: Rule, subject: dict[str, Any]) -> tuple[Verdict, float, str]:
        tags = {tag.lower() for tag in subject.get("tags") or []}
        paths = " ".join(subject.get("paths") or []).lower()
        summary = str(subject.get("summary") or "").lower()
        matched = bool(set(rule.match_tags) & tags) or any(tag in paths or tag in summary for tag in rule.match_tags)
        if not matched and rule.domain not in tags:
            return Verdict.ALLOW, 0.95, f"deterministic pre-check: rule '{rule.title}' not applicable"
        if SECRET.search(summary) or "secret" in tags:
            return Verdict.BLOCK, 1.0, f"deterministic pre-check blocked secret-bearing change for '{rule.title}'"
        if rule.domain in SENSITIVE_DOMAINS or tags & SENSITIVE_DOMAINS:
            return Verdict.BLOCK, 0.98, f"deterministic pre-check blocked sensitive change for '{rule.title}'"
        if tags & TASK_TRIGGERS:
            return Verdict.WARN, 0.9, f"deterministic pre-check warned for contract-impacting change under '{rule.title}'"
        return Verdict.ALLOW, 0.9, f"deterministic pre-check allowed change under '{rule.title}'"

    def _needs_semantic(self, rule: Rule, subject: dict[str, Any]) -> bool:
        tags = set(subject.get("tags") or [])
        return bool(tags & {"ambiguous", "refactor", "semantic"}) or rule.domain in {"compliance", "security"}

    def _is_sensitive(self, rule: Rule, subject: dict[str, Any]) -> bool:
        tags = set(subject.get("tags") or [])
        return rule.domain in SENSITIVE_DOMAINS or bool(tags & SENSITIVE_DOMAINS)

    def _rule_applies(self, rule: Rule, subject: dict[str, Any]) -> bool:
        tags = {tag.lower() for tag in subject.get("tags") or []}
        if not rule.match_tags:
            return True
        return bool(set(rule.match_tags) & tags) or rule.domain in tags

    def _detect_anomalies(self, scope: Scope, actor: str, correlation_id: str, subject: dict[str, Any], timestamp: str) -> list[AnomalySignal]:
        anomalies: list[AnomalySignal] = []
        paths = subject.get("paths") or []
        if len(paths) >= 8:
            anomaly = AnomalySignal(
                str(uuid4()),
                scope,
                actor,
                correlation_id,
                subject["subject_ref"],
                "unusually_many_files",
                min(1.0, len(paths) / 20),
                f"change touches {len(paths)} files",
                [subject["subject_ref"]],
                timestamp,
            )
            self.store.put_anomaly(anomaly)
            self.emit("AnomalyDetected", anomaly.public(), scope, actor, correlation_id, "", anomaly.id, anomaly.evidence_refs)
            anomalies.append(anomaly)
        tags = set(subject.get("tags") or [])
        if tags & SENSITIVE_DOMAINS and not subject.get("linked_task"):
            anomaly = AnomalySignal(
                str(uuid4()),
                scope,
                actor,
                correlation_id,
                subject["subject_ref"],
                "high_risk_without_task",
                0.8,
                "sensitive change without linked task",
                [subject["subject_ref"]],
                timestamp,
            )
            self.store.put_anomaly(anomaly)
            self.emit("AnomalyDetected", anomaly.public(), scope, actor, correlation_id, "", anomaly.id, anomaly.evidence_refs)
            anomalies.append(anomaly)
        return anomalies

    def _build_impact(self, scope: Scope, subject: dict[str, Any], timestamp: str) -> ImpactMap | None:
        tags = {tag.lower() for tag in subject.get("tags") or []}
        change_type = str(subject.get("change_type") or "").lower()
        affected: list[dict[str, Any]] = []
        if tags & {"api", "route", "contract"} or change_type == "api":
            affected.extend(
                [
                    {"entity": "frontend_clients", "relation": "depends_on", "confidence": 0.9},
                    {"entity": "mobile_clients", "relation": "depends_on", "confidence": 0.85},
                    {"entity": "api_docs", "relation": "explains", "confidence": 0.8},
                    {"entity": "contract_tests", "relation": "implements", "confidence": 0.88},
                ]
            )
        if tags & {"schema", "migration"} or change_type == "schema":
            affected.extend(
                [
                    {"entity": "dashboards", "relation": "depends_on", "confidence": 0.84},
                    {"entity": "migration_verification", "relation": "implements", "confidence": 0.9},
                    {"entity": "data_docs", "relation": "explains", "confidence": 0.75},
                ]
            )
        if not affected:
            return None
        risk = Severity.HIGH if tags & SENSITIVE_DOMAINS else Severity.MEDIUM
        impact = ImpactMap(str(uuid4()), scope, subject["subject_ref"], affected, risk, [], min(item["confidence"] for item in affected), timestamp)
        self.store.put_impact(impact)
        self.emit("ImpactMapCreated", impact.public(), scope, "system", subject.get("correlation_id") or "", "", impact.id, [subject["subject_ref"]])
        return impact

    def _route_tasks(
        self,
        scope: Scope,
        actor: str,
        correlation_id: str,
        subject: dict[str, Any],
        impact: ImpactMap | None,
        evaluations: list[RuleEvaluation],
        timestamp: str,
    ) -> list[RoutedTask]:
        if impact is None:
            return []
        blocked = any(item.verdict in {Verdict.BLOCK, Verdict.ESCALATE} and not item.shadow for item in evaluations)
        # Still generate downstream tasks for API/schema changes even when blocked — work must be planned.
        routes = {
            "frontend_clients": ("frontend", "Update frontend clients for API/schema change"),
            "mobile_clients": ("mobile", "Update mobile clients for API change"),
            "api_docs": ("docs", "Update API documentation"),
            "contract_tests": ("qa", "Update contract tests"),
            "dashboards": ("data", "Update dashboards for schema change"),
            "migration_verification": ("backend", "Verify data migration"),
            "data_docs": ("docs", "Update data documentation"),
        }
        tasks: list[RoutedTask] = []
        task_refs: list[str] = []
        for entity in impact.affected_entities:
            if entity["confidence"] < 0.8:
                continue
            assignee, title = routes.get(entity["entity"], ("platform", f"Review impact on {entity['entity']}"))
            existing = next(
                (task for task in self.store.list_tasks(scope) if task.subject_ref == subject["subject_ref"] and task.assignee_type == assignee),
                None,
            )
            if existing:
                tasks.append(existing)
                task_refs.append(existing.id)
                continue
            task = RoutedTask(
                str(uuid4()),
                scope,
                actor,
                correlation_id,
                subject["subject_ref"],
                title,
                assignee,
                f"impact:{entity['relation']}; blocked={blocked}",
                [subject["subject_ref"], impact.id],
                timestamp,
            )
            self.store.put_task(task)
            self.emit("TaskRouted", task.public(), scope, actor, correlation_id, "", task.id, task.evidence_refs)
            tasks.append(task)
            task_refs.append(task.id)
        impact.generated_task_refs = task_refs
        self.store.put_impact(impact)
        return tasks

    def _auto_request_approvals(
        self,
        scope: Scope,
        actor: str,
        correlation_id: str,
        evaluations: list[RuleEvaluation],
        timestamp: str,
    ) -> list[ApprovalRequest]:
        approvals: list[ApprovalRequest] = []
        for evaluation in evaluations:
            if evaluation.verdict != Verdict.ESCALATE:
                continue
            rule = self.store.get_rule(evaluation.rule_id, scope)
            approval = ApprovalRequest(
                str(uuid4()),
                scope,
                actor,
                correlation_id,
                evaluation.id,
                rule.id,
                rule.required_approval_role or rule.owner,
                ApprovalState.REQUESTED,
                ["approve", "reject", "needs_changes"],
                (datetime.now(UTC) + timedelta(hours=4 if rule.severity == Severity.CRITICAL else 24)).isoformat(),
                None,
                evaluation.evidence_refs,
                timestamp,
                timestamp,
            )
            self.store.put_approval(approval)
            self.emit("ApprovalRequested", approval.public(), scope, actor, correlation_id, "", approval.id, approval.evidence_refs)
            approvals.append(approval)
        return approvals

    def _evaluation_bundle(self, scope: Scope, subject: dict[str, Any], evaluations: list[RuleEvaluation], shadow: bool) -> dict[str, Any]:
        final = Verdict.ALLOW
        for evaluation in evaluations:
            if evaluation.verdict == Verdict.ESCALATE:
                final = Verdict.ESCALATE
                break
            if evaluation.verdict == Verdict.BLOCK and final != Verdict.ESCALATE:
                final = Verdict.BLOCK
            elif evaluation.verdict == Verdict.WARN and final == Verdict.ALLOW:
                final = Verdict.WARN
        return {
            "subject_ref": subject["subject_ref"],
            "shadow": shadow,
            "final_verdict": final.value,
            "blocked": final in {Verdict.BLOCK, Verdict.ESCALATE} and not shadow,
            "evaluations": [item.public() for item in evaluations],
        }

    def _replay_evaluation_bundle(
        self, scope: Scope, subject: dict[str, Any], evaluations: list[RuleEvaluation], shadow: bool
    ) -> dict[str, Any]:
        """Rebuild full evaluate response on idempotent retry (impact/tasks/approvals)."""
        bundle = self._evaluation_bundle(scope, subject, evaluations, shadow)
        subject_ref = subject["subject_ref"]
        impacts = [item for item in self.store.list_impacts(scope) if item.change_ref == subject_ref]
        evaluation_ids = {item.id for item in evaluations}
        bundle["impact"] = impacts[-1].public() if impacts else None
        bundle["tasks"] = [item.public() for item in self.store.list_tasks(scope) if item.subject_ref == subject_ref]
        bundle["approvals"] = [
            item.public() for item in self.store.list_approvals(scope) if item.evaluation_id in evaluation_ids
        ]
        bundle["anomalies"] = [
            item.public() for item in self.store.list_anomalies(scope) if item.subject_ref == subject_ref
        ]
        return bundle

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
                "producer": "rule-engine-service",
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


def tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9_-]*", value.lower())


def severity_score(severity: Severity) -> float:
    return {Severity.LOW: 0.25, Severity.MEDIUM: 0.5, Severity.HIGH: 0.75, Severity.CRITICAL: 1.0}[severity]
