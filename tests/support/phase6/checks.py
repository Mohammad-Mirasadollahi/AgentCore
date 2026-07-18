from __future__ import annotations

import sys
from typing import Any

from .catalog import ROOT
from .gate import CheckResult


def _ensure_paths() -> None:
    for relative in (
        "backend/services/core-data-service/src",
        "backend/services/memory-service/src",
        "backend/services/docs-sync-service/src",
        "backend/services/rule-engine-service/src",
        "backend/services/adapter-service/src",
    ):
        path = str(ROOT / relative)
        if path not in sys.path:
            sys.path.insert(0, path)


def verify_contracts() -> list[CheckResult]:
    _ensure_paths()
    from core_data_service.api import app as core_app
    from core_data_service.core import CoreData
    from core_data_service.testing import InMemoryStore as CoreStore
    from memory_service.api import app as memory_app
    from memory_service.core import MemoryService
    from memory_service.testing import InMemoryStore as MemoryStore
    from docs_sync_service.api import app as docs_app
    from docs_sync_service.core import DocsSyncService
    from docs_sync_service.testing import InMemoryStore as DocsStore
    from rule_engine_service.api import app as rules_app
    from rule_engine_service.core import RuleEngineService
    from rule_engine_service.testing import InMemoryStore as RulesStore
    from adapter_service.api import app as adapter_app
    from adapter_service.core import AdapterService
    from adapter_service.testing import InMemoryStore as AdapterStore

    results: list[CheckResult] = []
    suites = (
        ("core-data-service", core_app(CoreData(CoreStore())), "/api/v1/projects/{project_id}/activities"),
        ("memory-service", memory_app(MemoryService(MemoryStore())), "/api/v1/projects/{project_id}/memory-items"),
        ("docs-sync-service", docs_app(DocsSyncService(DocsStore())), "/api/v1/projects/{project_id}/symbols"),
        ("rule-engine-service", rules_app(RuleEngineService(RulesStore())), "/api/v1/projects/{project_id}/rules"),
        ("adapter-service", adapter_app(AdapterService(AdapterStore())), "/api/v1/projects/{project_id}/connectors"),
    )
    for subject, api, route in suites:
        routes = {item.path for item in api.routes}
        ok = route in routes
        results.append(
            CheckResult(
                f"contract-{subject}",
                "contract",
                subject,
                "passed" if ok else "failed",
                f"route {route} {'registered' if ok else 'missing'}",
                [route],
                "docs/06-technical-logic/07-technical-test-strategy.md",
            )
        )
    return results


def verify_state_machines() -> list[CheckResult]:
    _ensure_paths()
    from core_data_service.core import ConflictError, CoreData, Kind, Scope
    from core_data_service.testing import InMemoryStore

    service = CoreData(InMemoryStore())
    scope = Scope("t", "w", "p")
    task = service.create(
        Kind.TASK,
        scope,
        "agent",
        "corr",
        "task-1",
        {"title": "t", "assignee_type": "backend", "instructions": "do", "acceptance_criteria": ["ok"]},
    )
    try:
        service.transition(scope, "agent", "corr", "bad", task.id, "done", "skip", 1)
        return [CheckResult("state-illegal", "state_machine", "core-data-service", "failed", "illegal transition was accepted", [task.id])]
    except ConflictError:
        service.transition(scope, "agent", "corr", "ok", task.id, "ready", "triaged", 1)
        return [CheckResult("state-illegal", "state_machine", "core-data-service", "passed", "illegal transition rejected; legal transition accepted", [task.id])]


def verify_idempotency() -> list[CheckResult]:
    _ensure_paths()
    from core_data_service.core import CoreData, Kind, Scope
    from core_data_service.testing import InMemoryStore

    service = CoreData(InMemoryStore())
    scope = Scope("t", "w", "p")
    payload = {"action_type": "edit", "action_summary": "changed file"}
    first = service.create(Kind.ACTIVITY, scope, "agent", "corr", "idem-1", dict(payload))
    second = service.create(Kind.ACTIVITY, scope, "agent", "corr", "idem-1", dict(payload))
    ok = first.id == second.id
    return [
        CheckResult(
            "idempotency-activity",
            "idempotency",
            "core-data-service",
            "passed" if ok else "failed",
            "duplicate idempotency key reused same record" if ok else "duplicate created distinct records",
            [first.id, second.id],
        )
    ]


def verify_redaction() -> list[CheckResult]:
    _ensure_paths()
    from memory_service.core import MemoryService, Scope
    from memory_service.testing import InMemoryStore

    service = MemoryService(InMemoryStore())
    scope = Scope("t", "w", "p")
    item = service.create_memory(
        scope,
        "agent",
        "corr",
        "secret-1",
        {
            "kind": "restricted",
            "title": "Secret",
            "body": "token=super-secret-value must never enter prompts",
            "tags": ["security"],
            "evidence_refs": ["e1"],
            "source_refs": ["s1"],
            "confidence": 0.9,
        },
    )
    body = item.public()["body"]
    ok = "super-secret-value" not in body and "[REDACTED]" in body
    return [
        CheckResult(
            "redaction-memory",
            "redaction",
            "memory-service",
            "passed" if ok else "failed",
            "secret token redacted" if ok else "secret token leaked",
            [item.id],
        )
    ]


def run_all_checks() -> list[CheckResult]:
    results: list[CheckResult] = []
    results.extend(verify_contracts())
    results.extend(verify_state_machines())
    results.extend(verify_idempotency())
    results.extend(verify_redaction())
    return results


def checks_public(results: list[CheckResult]) -> list[dict[str, Any]]:
    return [item.public() for item in results]
