from adapter_service.api import app
from adapter_service.core import AdapterService, Scope
from adapter_service.testing import InMemoryStore


SCOPE = Scope("t", "w", "p")


def universal(sender: str, intent: str, status: str, refs=None, **payload):
    return {
        "message_id": f"msg-{sender}-{intent}",
        "schema_version": "1.0.0",
        "sender": sender,
        "sender_type": "agent",
        "tenant_id": "t",
        "project_id": "p",
        "intent": intent,
        "domain": "engineering",
        "payload": payload or {"summary": intent},
        "status": status,
        "refs": refs or [],
        "correlation_id": "corr-1",
        "created_at": "2026-07-18T12:00:00+00:00",
    }


def ready_connector(service: AdapterService, key: str, vendor: str):
    connector = service.register_connector(
        SCOPE,
        "ops",
        "corr",
        key,
        {
            "vendor": vendor,
            "name": f"{vendor}-agent",
            "capabilities": ["can_edit_code", "can_report_task_state"],
            "auth_profile": "token",
            "credential": f"{vendor}-secret",
        },
    )
    return service.validate_connector(SCOPE, "ops", "corr", key + "-validate", connector.id)


def test_two_vendors_exchange_task_state_and_ide_receives_api_ready():
    store = InMemoryStore()
    service = AdapterService(store)

    vendor_a = ready_connector(service, "conn-a", "acme")
    vendor_b = ready_connector(service, "conn-b", "globex")
    assert {item["vendor"] for item in service.discover_capabilities(SCOPE)} == {"acme", "globex"}

    peer = service.subscribe(
        SCOPE,
        "ops",
        "corr",
        "sub-peer",
        {
            "channel": "agent.tasks",
            "subscriber_type": "agent",
            "endpoint": f"vendor://{vendor_b.vendor}/inbox",
            "filter_intents": ["TASK_STARTED", "TASK_COMPLETED"],
        },
    )
    ide = service.subscribe(
        SCOPE,
        "ops",
        "corr",
        "sub-ide",
        {
            "channel": "ide.notifications",
            "subscriber_type": "ide",
            "endpoint": "ide://plugin/notifications",
            "filter_intents": ["API_READY"],
        },
    )

    normalized = service.normalize_vendor_event(
        SCOPE,
        "ops",
        "corr",
        "norm-1",
        vendor_a.id,
        {"id": "v1", "intent": "TASK_STARTED", "status": "running", "task_id": "task-9", "summary": "started"},
    )
    published = service.publish_agent_event(SCOPE, "ops", "corr", "pub-1", normalized["message"])
    assert published["channel"] == "agent.tasks"
    delivered_subs = {item["subscription_id"] for item in published["deliveries"] if item["status"] == "delivered"}
    assert peer.id in delivered_subs

    api_ready = service.publish_agent_event(
        SCOPE,
        "ops",
        "corr",
        "pub-2",
        universal("acme", "API_READY", "completed", refs=["api:/v1/users"], summary="Users API ready"),
    )
    assert api_ready["channel"] == "ide.notifications"
    assert any(item["subscription_id"] == ide.id and item["status"] == "delivered" for item in api_ready["deliveries"])
    assert any(event["event_type"] == "IdeNotificationSent" for event in store.outbox())


def test_dead_letter_replay_and_code_release_department_tasks():
    store = InMemoryStore()
    service = AdapterService(store)
    connector = ready_connector(service, "conn-a", "acme")

    failing = service.subscribe(
        SCOPE,
        "ops",
        "corr",
        "sub-fail",
        {
            "channel": "department.workflows",
            "subscriber_type": "webhook",
            "endpoint": "https://example.invalid/hook",
            "fail_mode": "always",
        },
    )
    result = service.publish_agent_event(
        SCOPE,
        "ops",
        "corr",
        "pub-release",
        universal("acme", "CODE_RELEASED", "completed", refs=["release:1.2.0"], summary="backend release"),
    )
    assert result["channel"] == "department.workflows"
    assert any(item["subscription_id"] == failing.id and item["status"] == "dead_lettered" for item in result["deliveries"])
    assert service.get_dead_letter_queue(SCOPE)
    departments = {task.department for task in service.list_department_tasks(SCOPE)}
    assert {"marketing", "support", "devops"} <= departments

    replayed = service.replay(SCOPE, "ops", "corr", "replay-1", "department.workflows")
    assert replayed["replayed_count"] == 1

    ticket = service.create_external_ticket(
        SCOPE,
        "ops",
        "corr",
        "ticket-1",
        {"connector_id": connector.id, "title": "Announce release", "department": "marketing", "source_event_id": result["event"]["id"]},
    )
    synced = service.sync_external_status(SCOPE, "ops", "corr", "sync-1", ticket.id, "done")
    assert synced.status.value == "done"
    assert service.list_department_tasks(Scope("other", "w", "p")) == []


def test_api_contract_routes_are_registered():
    routes = {route.path for route in app(AdapterService(InMemoryStore())).routes}
    assert "/api/v1/projects/{project_id}/connectors" in routes
    assert "/api/v1/projects/{project_id}/agent-events" in routes
    assert "/api/v1/projects/{project_id}/dead-letters" in routes
    assert "/api/v1/projects/{project_id}/department-tasks" in routes
