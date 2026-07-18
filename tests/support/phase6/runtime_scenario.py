from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .checks import _ensure_paths


@dataclass
class RuntimeScenarioReport:
    scenario_id: str
    status: str
    correlation_id: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)

    def public(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "status": self.status,
            "correlation_id": self.correlation_id,
            "steps": self.steps,
            "evidence_refs": self.evidence_refs,
            "passed": self.status == "passed",
        }


def run_runtime_scenario(correlation_id: str = "corr-phase6-runtime") -> RuntimeScenarioReport:
    """
    Stitch Phases 1 through 5 in-process:

    activity/worklog/decision/issue/task -> memory -> docs drift -> rules escalate -> broker department tasks
    """
    _ensure_paths()
    from core_data_service.core import CoreData, Kind
    from core_data_service.core import Scope as CoreScope
    from core_data_service.testing import InMemoryStore as CoreStore
    from memory_service.core import MemoryService
    from memory_service.core import Scope as MemoryScope
    from memory_service.testing import InMemoryStore as MemoryStore
    from docs_sync_service.core import DocsSyncService
    from docs_sync_service.core import Scope as DocsScope
    from docs_sync_service.testing import InMemoryStore as DocsStore
    from rule_engine_service.core import RuleEngineService
    from rule_engine_service.core import Scope as RulesScope
    from rule_engine_service.testing import InMemoryStore as RulesStore
    from adapter_service.core import AdapterService
    from adapter_service.core import Scope as AdapterScope
    from adapter_service.testing import InMemoryStore as AdapterStore

    steps: list[dict[str, Any]] = []
    evidence: list[str] = []
    actor = "phase6-agent"

    core = CoreData(CoreStore())
    core_scope = CoreScope("t", "w", "p")
    activity = core.create(
        Kind.ACTIVITY,
        core_scope,
        actor,
        correlation_id,
        "rt-activity",
        {"action_type": "edit", "action_summary": "migrate password hashing to Argon2", "evidence_refs": ["diff-auth"]},
    )
    worklog = core.create(
        Kind.WORK_LOG,
        core_scope,
        actor,
        correlation_id,
        "rt-worklog",
        {"session_id": "sess-1", "agent_id": actor, "summary": "Prepared Argon2 migration"},
    )
    decision = core.create(
        Kind.DECISION,
        core_scope,
        actor,
        correlation_id,
        "rt-decision",
        {
            "title": "Use Argon2",
            "context": "password hashing",
            "options_considered": ["sha256", "argon2"],
            "chosen_option": "argon2",
            "consequences": ["slower hashes", "stronger resistance"],
            "owner": "security",
            "status": "active",
        },
    )
    issue, tasks = core.create_issue(
        core_scope,
        actor,
        correlation_id,
        "rt-issue",
        {
            "title": "Legacy SHA256 password hashes remain",
            "description": "Old users may fail login after Argon2 cutover",
            "severity": "critical",
            "evidence_refs": ["diff-auth", decision.id],
            "task_specs": [
                {
                    "title": "Add dual-hash login fallback",
                    "assignee_type": "backend",
                    "instructions": "accept sha256 then upgrade",
                    "acceptance_criteria": ["login works for old hashes"],
                }
            ],
        },
    )
    steps.append({"phase": 1, "activity_id": activity.id, "worklog_id": worklog.id, "decision_id": decision.id, "issue_id": issue.id, "task_ids": [task.id for task in tasks]})
    evidence.extend(["diff-auth", activity.id, worklog.id, decision.id, issue.id, *[task.id for task in tasks]])

    memory = MemoryService(MemoryStore())
    memory_scope = MemoryScope("t", "w", "p")
    memory_item = memory.create_memory(
        memory_scope,
        actor,
        correlation_id,
        "rt-memory",
        {
            "kind": "semantic",
            "title": "Password hashing current state",
            "body": "PaymentGateway unchanged. Password hashing target is Argon2.",
            "tags": ["security", "auth", "argon2"],
            "evidence_refs": [decision.id],
            "source_refs": [worklog.id],
            "confidence": 0.95,
        },
    )
    bundle = memory.retrieve_context(memory_scope, actor, correlation_id, "argon2 password hashing auth", token_budget=120)
    steps.append({"phase": 2, "memory_id": memory_item.id, "bundle_id": bundle.bundle_id, "selected": len(bundle.items)})
    evidence.append(memory_item.id)

    docs = DocsSyncService(DocsStore())
    docs_scope = DocsScope("t", "w", "p")
    symbol = docs.index_symbol(
        docs_scope,
        actor,
        correlation_id,
        "rt-symbol",
        {
            "repo": "agentcore",
            "file_path": "src/auth.py",
            "symbol_path": "auth.hash_password",
            "kind": "function",
            "body": "def hash_password(value):\n    return sha256(value)\n",
            "tags": ["auth", "security"],
            "doc_required": True,
        },
    )
    document = docs.index_document(
        docs_scope,
        actor,
        correlation_id,
        "rt-doc",
        {
            "path": "docs/auth.md",
            "frontmatter": {
                "doc_id": "doc-auth-hash",
                "title": "Password hashing",
                "owner": "security",
                "status": "active",
                "schema_version": "1.0.0",
                "linked_symbols": ["auth.hash_password"],
                "decision_refs": [decision.id],
            },
            "body": "Uses SHA256 today.",
        },
    )
    docs.register_anchor(
        docs_scope,
        actor,
        correlation_id,
        "rt-anchor",
        {"doc_id": document.id, "symbol_id": symbol.id, "recorded_hash": symbol.body_hash},
    )
    docs.index_symbol(
        docs_scope,
        actor,
        correlation_id,
        "rt-symbol-2",
        {
            "repo": "agentcore",
            "file_path": "src/auth.py",
            "symbol_path": "auth.hash_password",
            "kind": "function",
            "body": "def hash_password(value):\n    return argon2(value)\n",
            "tags": ["auth", "security"],
            "doc_required": True,
        },
    )
    findings = docs.detect_drift(docs_scope, actor, correlation_id, "rt-drift", [symbol.id])
    steps.append({"phase": 3, "symbol_id": symbol.id, "document_id": document.id, "findings": [item.id for item in findings]})
    evidence.extend([symbol.id, document.id, *[item.id for item in findings]])

    rules = RuleEngineService(RulesStore())
    rules_scope = RulesScope("t", "w", "p")
    rules.create_rule(
        rules_scope,
        actor,
        correlation_id,
        "rt-rule",
        {
            "title": "Auth changes require approval",
            "natural_language_rule": "Authentication and security production changes require human approval",
            "severity": "critical",
            "owner": "security-lead",
            "evaluation_mode": "hybrid",
            "domain": "security",
            "match_tags": ["security", "auth", "production"],
            "required_approval_role": "security-approver",
        },
    )
    evaluation = rules.evaluate_rules(
        rules_scope,
        actor,
        correlation_id,
        "rt-eval",
        {
            "subject_ref": symbol.id,
            "summary": "Migrate production auth hashing to Argon2",
            "change_type": "code",
            "tags": ["security", "auth", "production"],
            "paths": ["src/auth.py"],
            "evidence_refs": [decision.id, "diff-auth"],
        },
    )
    steps.append({"phase": 4, "final_verdict": evaluation["final_verdict"], "blocked": evaluation["blocked"], "approvals": len(evaluation["approvals"])})
    evidence.extend([item["id"] for item in evaluation["evaluations"]])

    adapter = AdapterService(AdapterStore())
    adapter_scope = AdapterScope("t", "w", "p")
    connector = adapter.register_connector(
        adapter_scope,
        actor,
        correlation_id,
        "rt-connector",
        {
            "vendor": "acme",
            "name": "acme-agent",
            "capabilities": ["can_edit_code", "can_report_task_state"],
            "auth_profile": "token",
            "credential": "phase6-secret",
        },
    )
    adapter.validate_connector(adapter_scope, actor, correlation_id, "rt-connector-validate", connector.id)
    adapter.subscribe(
        adapter_scope,
        actor,
        correlation_id,
        "rt-sub-dept",
        {"channel": "department.workflows", "subscriber_type": "webhook", "endpoint": "https://example.invalid/hooks"},
    )
    published = adapter.publish_agent_event(
        adapter_scope,
        actor,
        correlation_id,
        "rt-publish",
        {
            "message_id": "msg-phase6-release",
            "schema_version": "1.0.0",
            "sender": "acme",
            "sender_type": "agent",
            "tenant_id": "t",
            "project_id": "p",
            "intent": "CODE_RELEASED",
            "domain": "engineering",
            "payload": {"summary": "Argon2 migration released", "decision_id": decision.id},
            "status": "completed",
            "refs": [decision.id, issue.id],
            "correlation_id": correlation_id,
            "created_at": activity.created_at,
        },
    )
    departments = {task["department"] for task in published["department_tasks"]}
    steps.append({"phase": 5, "event_id": published["event"]["id"], "departments": sorted(departments)})
    evidence.append(published["event"]["id"])

    ok = (
        activity.correlation_id == correlation_id
        and worklog.correlation_id == correlation_id
        and decision.correlation_id == correlation_id
        and issue.correlation_id == correlation_id
        and findings
        and evaluation["blocked"] is True
        and evaluation["approvals"]
        and {"marketing", "support", "devops"} <= departments
        and all(ref for ref in evidence)
    )
    return RuntimeScenarioReport(
        "password-hashing-migration",
        "passed" if ok else "failed",
        correlation_id,
        steps,
        evidence,
    )
