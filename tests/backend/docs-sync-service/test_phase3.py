from docs_sync_service.api import app
from docs_sync_service.core import DocsSyncService, Scope, digest, normalize_source
from docs_sync_service.testing import InMemoryStore


SCOPE = Scope("t", "w", "p")


def symbol_payload(path="auth.login", kind="function", body="def login():\n    return True\n", **extra):
    return {
        "repo": "agentcore",
        "file_path": "src/auth.py",
        "symbol_path": path,
        "kind": kind,
        "body": body,
        "doc_required": extra.pop("doc_required", True),
        "tags": extra.pop("tags", ["auth", "security"]),
        **extra,
    }


def frontmatter(doc_id="doc-login", symbols=None):
    return {
        "doc_id": doc_id,
        "title": "Login documentation",
        "owner": "platform",
        "status": "active",
        "schema_version": "1.0.0",
        "linked_symbols": symbols or ["auth.login"],
        "decision_refs": ["decision-1"],
    }


def test_stale_doc_drift_ci_gate_and_issue_task_refs():
    store = InMemoryStore()
    service = DocsSyncService(store)

    original = "def login():\n    return check_password()\n"
    symbol = service.index_symbol(SCOPE, "agent", "corr", "sym-1", symbol_payload(body=original))
    document = service.index_document(
        SCOPE,
        "agent",
        "corr",
        "doc-1",
        {"path": "docs/login.md", "frontmatter": frontmatter(), "body": "Login flow."},
    )
    assert service.index_document(
        SCOPE,
        "agent",
        "corr",
        "doc-1",
        {"path": "docs/login.md", "frontmatter": frontmatter(), "body": "Login flow."},
    ).id == document.id

    service.register_anchor(
        SCOPE,
        "agent",
        "corr",
        "anchor-1",
        {"doc_id": document.id, "symbol_id": symbol.id, "recorded_hash": symbol.body_hash},
    )

    changed = service.index_symbol(
        SCOPE,
        "agent",
        "corr",
        "sym-2",
        symbol_payload(body="def login():\n    return check_password() and mfa()\n"),
    )
    findings = service.detect_drift(SCOPE, "agent", "corr", "drift-1", [changed.id])
    assert len(findings) == 1
    assert findings[0].drift_type.value == "stale_doc"
    assert findings[0].severity.value == "critical"
    assert findings[0].issue_ref.startswith("issue:")
    assert findings[0].task_ref.startswith("task:docs-agent:")
    assert store.outbox()[-1]["event_type"] == "DocumentationDriftDetected"

    gate = service.evaluate_ci_gate(SCOPE)
    assert gate["decision"] == "fail"
    assert gate["blockers"][0]["id"] == findings[0].id

    waived = service.evaluate_ci_gate(SCOPE, [findings[0].id])
    assert waived["decision"] == "pass"

    other = service.list_drift_findings(Scope("other", "w", "p"))
    assert other == []


def test_missing_doc_bloom_frontmatter_and_draft_approval():
    store = InMemoryStore()
    service = DocsSyncService(store)

    symbol = service.index_symbol(SCOPE, "agent", "corr", "sym-1", symbol_payload(tags=["api", "route"], kind="route"))
    assert service.find_missing_docs(SCOPE)[0]["symbol"]["id"] == symbol.id

    bloom = service.bloom_lookup(SCOPE, symbol.id)
    assert bloom["definite_no_doc"] is True
    assert bloom["maybe_documented"] is False

    errors = service.validate_frontmatter({"title": "x"})
    assert "missing required field: doc_id" in errors

    findings = service.detect_drift(SCOPE, "agent", "corr", "drift-missing", [symbol.id])
    assert findings[0].drift_type.value == "missing_doc"
    assert findings[0].severity.value == "high"

    draft = service.create_draft(
        SCOPE,
        "agent",
        "corr",
        "draft-1",
        {"symbol_id": symbol.id, "title": "Route docs", "body": "Describe the route.", "finding_id": findings[0].id},
    )
    approved = service.approve_draft(SCOPE, "agent", "corr", "approve-1", draft.id)
    assert approved.state.value == "approved"
    assert store.outbox()[-1]["event_type"] == "DocumentationDraftApproved"


def test_normalization_ignores_formatting_noise():
    left = normalize_source("def login():\n    return True  # note\n")
    right = normalize_source("def login():\n\n    return    True\n")
    assert left == right
    assert digest(left) == digest(right)


def test_api_contract_routes_are_registered():
    routes = {route.path for route in app(DocsSyncService(InMemoryStore())).routes}
    assert "/api/v1/projects/{project_id}/symbols" in routes
    assert "/api/v1/projects/{project_id}/documents" in routes
    assert "/api/v1/projects/{project_id}/drift-detections" in routes
    assert "/api/v1/projects/{project_id}/drafts/{draft_id}:approve" in routes
    assert "/api/v1/projects/{project_id}/ci-gate" in routes
