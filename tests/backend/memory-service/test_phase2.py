from memory_service.api import app
from memory_service.core import MemoryService, Scope
from memory_service.testing import InMemoryStore


SCOPE = Scope("t", "w", "p")


def memory(kind="semantic", title="Current architecture rule", body="Use dependency injection for memory retrieval.", **extra):
    return {
        "kind": kind,
        "title": title,
        "body": body,
        "tags": extra.pop("tags", ["architecture", "memory"]),
        "evidence_refs": extra.pop("evidence_refs", ["decision-1"]),
        "source_refs": extra.pop("source_refs", ["worklog-1"]),
        "confidence": extra.pop("confidence", 0.9),
        **extra,
    }


def test_consolidation_retrieval_scope_and_restricted_boundary():
    store = InMemoryStore()
    service = MemoryService(store)

    created = service.create_memory(SCOPE, "agent", "corr", "one", memory())
    assert service.create_memory(SCOPE, "agent", "corr", "one", memory()).id == created.id

    restricted = service.create_memory(
        SCOPE,
        "agent",
        "corr",
        "restricted",
        memory("restricted", "Secret token rule", "token=hidden must never enter prompts."),
    )
    assert "hidden" not in restricted.public()["body"]

    consolidated = service.consolidate_memory(SCOPE, "agent", "corr", "consolidate", [created.id], "phase boundary")
    assert consolidated[0].state.value == "active"

    bundle = service.retrieve_context(SCOPE, "agent", "corr", "memory dependency injection architecture", token_budget=80).public()
    assert [item["memory"]["id"] for item in bundle["items"]] == [created.id]
    assert {item["reason"] for item in bundle["excluded"]} >= {"restricted_memory_boundary"}

    other_tenant = service.retrieve_context(Scope("other", "w", "p"), "agent", "corr", "memory dependency injection architecture").public()
    assert other_tenant["items"] == []
    assert store.outbox()[-1]["event_type"] == "ContextBundleBuilt"


def test_repeated_question_normalization_and_faq_promotion_requires_evidence():
    service = MemoryService(InMemoryStore())

    first = service.observe_question(SCOPE, "agent", "corr", "q1", "How do we build context bundles?", ["doc-1"])
    second = service.observe_question(SCOPE, "agent", "corr", "q2", "how do we build context bundles", ["doc-2"])
    assert first.id == second.id
    assert second.observations == 2

    repeated = service.list_repeated_questions(SCOPE)
    assert repeated[0].normalized_question == "how do we build context bundles"

    promoted = service.promote_faq(SCOPE, "agent", "corr", "faq", second.id, "Use scoped retrieval, evidence, weights, and token budgets.")
    assert promoted.state.value == "approved_faq"


def test_work_batch_ready_state_and_event_contract():
    store = InMemoryStore()
    service = MemoryService(store)

    item = service.create_memory(SCOPE, "agent", "corr", "one", memory())
    batch = service.open_batch(SCOPE, "agent", "corr", "batch", "phase boundary", [item.id], ["memory_consolidation"])

    ready = service.mark_batch_ready(SCOPE, "agent", "corr", "ready", batch.id, "meaningful work boundary")
    assert ready.state.value == "ready_for_consolidation"
    assert store.get_batch(batch.id, SCOPE).state.value == "ready_for_consolidation"

    event = store.outbox()[-1]
    assert event["event_type"] == "BatchReadyForConsolidation"
    assert event["event_version"] == 1
    assert event["producer"] == "memory-service"
    assert event["tenant_id"] == "t"
    assert event["project_id"] == "p"


def test_api_contract_routes_are_registered():
    routes = {route.path for route in app(MemoryService(InMemoryStore())).routes}
    assert "/api/v1/projects/{project_id}/memory-items" in routes
    assert "/api/v1/projects/{project_id}/context-bundles" in routes
    assert "/api/v1/projects/{project_id}/question-memories/{question_id}:promote-faq" in routes
