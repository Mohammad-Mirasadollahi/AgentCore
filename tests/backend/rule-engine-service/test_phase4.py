from rule_engine_service.api import app
from rule_engine_service.core import RuleEngineService, Scope
from rule_engine_service.testing import InMemoryStore


SCOPE = Scope("t", "w", "p")


def security_rule(**extra):
    return {
        "title": "Block unsafe production auth changes",
        "natural_language_rule": "Production authentication and security changes require human approval",
        "severity": "critical",
        "owner": "security-lead",
        "evaluation_mode": "hybrid",
        "domain": "security",
        "match_tags": ["security", "auth", "production"],
        "examples": ["changed auth middleware without approval"],
        "counterexamples": ["docs-only edit"],
        "required_approval_role": "security-approver",
        "precedence": 200,
        **extra,
    }


def test_sensitive_change_blocks_for_approval_with_rationale_and_evidence():
    store = InMemoryStore()
    service = RuleEngineService(store)

    rule = service.create_rule(SCOPE, "agent", "corr", "rule-1", security_rule())
    assert service.create_rule(SCOPE, "agent", "corr", "rule-1", security_rule()).id == rule.id

    result = service.evaluate_rules(
        SCOPE,
        "agent",
        "corr",
        "eval-1",
        {
            "subject_ref": "change-auth-1",
            "summary": "Update production auth middleware",
            "change_type": "code",
            "tags": ["security", "auth", "production"],
            "paths": ["src/auth/middleware.py"],
            "evidence_refs": ["diff-1"],
        },
    )
    assert result["blocked"] is True
    assert result["final_verdict"] == "escalate"
    evaluation = result["evaluations"][0]
    assert evaluation["rationale"]
    assert "diff-1" in evaluation["evidence_refs"]
    assert result["approvals"]
    assert result["approvals"][0]["status"] == "requested"
    assert service.get_approval_queue(SCOPE)[0].id == result["approvals"][0]["id"]

    resolved = service.resolve_approval(
        SCOPE,
        "human",
        "corr",
        "resolve-1",
        result["approvals"][0]["id"],
        "approved",
        "temporary waiver with rollback plan",
    )
    assert resolved.status.value == "approved"
    assert store.outbox()[-1]["event_type"] == "ApprovalResolved"
    assert service.list_evaluations(Scope("other", "w", "p")) == []


def test_api_schema_change_routes_downstream_tasks_and_semantic_evidence():
    store = InMemoryStore()
    service = RuleEngineService(store)
    service.create_rule(
        SCOPE,
        "agent",
        "corr",
        "rule-api",
        {
            "title": "API contract changes need downstream updates",
            "natural_language_rule": "Public API and schema changes must update clients docs and tests",
            "severity": "high",
            "owner": "platform",
            "evaluation_mode": "semantic",
            "domain": "engineering",
            "match_tags": ["api", "schema"],
            "examples": ["openapi field removed"],
            "precedence": 150,
        },
    )

    result = service.evaluate_rules(
        SCOPE,
        "agent",
        "corr",
        "eval-api",
        {
            "subject_ref": "change-api-1",
            "summary": "Remove field from public API schema",
            "change_type": "api",
            "tags": ["api", "schema", "contract"],
            "paths": ["openapi.yaml", "migrations/0002.sql"],
            "evidence_refs": ["pr-22"],
            "linked_task": "task-existing",
        },
    )
    assert result["impact"] is not None
    assignees = {task["assignee_type"] for task in result["tasks"]}
    assert {"frontend", "docs", "qa", "data", "backend"} <= assignees
    semantic = [item for item in result["evaluations"] if item["used_llm"]]
    assert semantic
    assert semantic[0]["rationale"]
    assert "pr-22" in semantic[0]["evidence_refs"]

    feedback = service.record_feedback(SCOPE, "agent", "corr", "fb-1", semantic[0]["id"], "true_positive", "correct block")
    assert feedback.label == "true_positive"
    assert any(event["event_type"] == "TaskRouted" for event in store.outbox())


def test_low_risk_deterministic_allow_and_shadow_mode():
    service = RuleEngineService(InMemoryStore())
    service.create_rule(
        SCOPE,
        "agent",
        "corr",
        "rule-docs",
        {
            "title": "Docs only changes are low risk",
            "natural_language_rule": "Documentation-only edits are allowed",
            "severity": "low",
            "owner": "docs",
            "evaluation_mode": "deterministic",
            "domain": "engineering",
            "match_tags": ["docs"],
            "state": "shadow",
        },
    )
    shadow = service.run_shadow(
        SCOPE,
        "agent",
        "corr",
        "shadow-1",
        {"subject_ref": "change-docs-1", "summary": "Fix typo", "tags": ["docs"], "paths": ["README.md"]},
    )
    assert shadow["shadow"] is True
    assert shadow["blocked"] is False
    assert shadow["final_verdict"] == "allow"


def test_api_contract_routes_are_registered():
    routes = {route.path for route in app(RuleEngineService(InMemoryStore())).routes}
    assert "/api/v1/projects/{project_id}/rules" in routes
    assert "/api/v1/projects/{project_id}/evaluations" in routes
    assert "/api/v1/projects/{project_id}/approvals/{approval_id}:resolve" in routes
    assert "/api/v1/projects/{project_id}/rule-health" in routes
