import asyncio

from httpx import ASGITransport, AsyncClient

from core_data_service.api import app
from core_data_service.core import CoreData, Kind, Scope
from core_data_service.testing import InMemoryStore


H = {"X-Tenant-Id": "t", "X-Workspace-Id": "w", "X-Actor-Id": "agent", "Idempotency-Key": "one"}


class ApiClient:
    def __init__(self, api):
        self.api = api

    def request(self, method: str, url: str, **kwargs):
        async def execute():
            async with AsyncClient(transport=ASGITransport(app=self.api), base_url="http://test") as client:
                return await client.request(method, url, **kwargs)

        return asyncio.run(execute())

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)


def task():
    return {"title": "implement store", "assignee_type": "backend", "instructions": "write it", "acceptance_criteria": ["tests"]}


def decision():
    return {
        "title": "records persist",
        "context": "phase one",
        "options_considered": ["db", "files"],
        "chosen_option": "db",
        "consequences": ["migrations"],
        "owner": "platform",
    }


def test_idempotent_task_transition_scope_and_task_board():
    store = InMemoryStore()
    client = ApiClient(app(CoreData(store)))
    url = "/api/v1/projects/p/tasks"

    created = client.post(url, headers=H, json=task())
    assert created.status_code == 200
    assert client.post(url, headers=H, json=task()).json()["record"]["id"] == created.json()["record"]["id"]

    task_id = created.json()["record"]["id"]
    transitioned = client.post(
        url + "/" + task_id + ":transition",
        headers={**H, "Idempotency-Key": "two"},
        json={"status": "ready", "reason": "triaged", "expected_version": 1},
    )
    assert transitioned.json()["task"]["status"] == "ready"
    assert client.get(url, headers={**H, "X-Tenant-Id": "other"}).json()["items"] == []
    assert client.get("/api/v1/projects/p/task-board", headers=H).json()["board"]["ready"][0]["id"] == task_id
    assert store.outbox()[-1]["event_type"] == "task.state_changed"


def test_decision_supersession_keeps_old_record_through_api():
    service = CoreData(InMemoryStore())
    client = ApiClient(app(service))
    created = client.post("/api/v1/projects/p/decisions", headers={**H, "Idempotency-Key": "d1"}, json={**decision(), "status": "active"})
    old_id = created.json()["record"]["id"]

    superseded = client.post(
        f"/api/v1/projects/p/decisions/{old_id}:supersede",
        headers={**H, "Idempotency-Key": "d2"},
        json={**decision(), "title": "records persist in postgres later"},
    )
    assert superseded.status_code == 200
    assert superseded.json()["decision"]["status"] == "active"
    assert service.store.get(old_id, Scope("t", "w", "p")).status == "superseded"
    history = client.get("/api/v1/projects/p/decision-history", headers=H).json()["items"]
    assert {item["status"] for item in history} == {"active", "superseded"}


def test_critical_issue_requires_task_or_escalation_and_can_create_tasks():
    client = ApiClient(app(CoreData(InMemoryStore())))
    issue = {"title": "production outage", "description": "api is down", "severity": "critical", "evidence_refs": ["incident-1"]}

    rejected = client.post("/api/v1/projects/p/issues", headers=H, json=issue)
    assert rejected.status_code == 400
    assert "task_specs or escalation_reason" in rejected.text

    accepted = client.post(
        "/api/v1/projects/p/issues",
        headers={**H, "Idempotency-Key": "critical-1", "X-Correlation-Id": "corr-critical"},
        json={**issue, "task_specs": [task()]},
    )
    assert accepted.status_code == 200
    issue_id = accepted.json()["record"]["id"]
    assert accepted.json()["tasks"][0]["data"]["issue_id"] == issue_id
    assert client.get("/api/v1/projects/p/open-issues", headers=H).json()["items"][0]["id"] == issue_id
    assert client.get("/api/v1/projects/p/evidence-bundles/incident-1", headers=H).json()["items"][0]["id"] == issue_id
    related = client.get("/api/v1/projects/p/related-work?correlation_id=corr-critical", headers=H).json()["items"]
    assert {item["kind"] for item in related} == {"issue", "task"}


def test_redaction_validation_and_event_contract():
    store = InMemoryStore()
    client = ApiClient(app(CoreData(store)))
    response = client.post(
        "/api/v1/projects/p/activities",
        headers=H,
        json={"action_type": "command", "action_summary": "token=hidden", "evidence_refs": ["cmd-1"]},
    )
    assert response.status_code == 200
    assert "hidden" not in response.text
    assert client.post("/api/v1/projects/p/tasks", json=task()).status_code == 400

    event = store.outbox()[0]
    assert event["event_type"] == "activity.recorded"
    assert event["event_version"] == 1
    assert event["source"] == "core-data-service"
    assert event["tenant_id"] == "t"
    assert event["evidence_refs"] == ["cmd-1"]
