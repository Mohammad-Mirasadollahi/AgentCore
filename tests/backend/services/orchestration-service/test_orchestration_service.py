import asyncio

from httpx import ASGITransport, AsyncClient

from orchestration_service.api import app
from orchestration_service.core import OrchestrationService
from orchestration_service.testing import InMemoryStore


H = {"X-Tenant-Id": "t", "X-Workspace-Id": "w", "X-Actor-Id": "orch", "Idempotency-Key": "one"}


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


def test_open_batch_route_and_close():
    store = InMemoryStore()
    client = ApiClient(app(OrchestrationService(store)))
    batch = client.post("/api/v1/projects/p/work-batches", headers=H, json={"title": "migration", "task_ids": ["t1"]})
    assert batch.status_code == 200
    batch_id = batch.json()["batch"]["id"]
    routed = client.post(
        "/api/v1/projects/p/assignments",
        headers={**H, "Idempotency-Key": "two"},
        json={"task_id": "t1", "agent_type": "backend", "batch_id": batch_id},
    )
    assert routed.json()["assignment"]["status"] == "assigned"
    closed = client.post(f"/api/v1/projects/p/work-batches/{batch_id}:close", headers=H)
    assert closed.json()["batch"]["status"] == "closed"
    assert any(e["event_type"] == "task.routed" for e in store.outbox())


def test_idempotent_batch_open():
    client = ApiClient(app(OrchestrationService(InMemoryStore())))
    a = client.post("/api/v1/projects/p/work-batches", headers=H, json={"title": "x"})
    b = client.post("/api/v1/projects/p/work-batches", headers=H, json={"title": "x"})
    assert a.json()["batch"]["id"] == b.json()["batch"]["id"]


def test_route_requires_task_and_agent():
    client = ApiClient(app(OrchestrationService(InMemoryStore())))
    bad = client.post("/api/v1/projects/p/assignments", headers=H, json={"task_id": ""})
    assert bad.status_code == 400


def test_complete_assignment_and_list(tmp_path):
    from orchestration_service.core import Scope
    from orchestration_service.testing import DictStore

    path = tmp_path / "orch.json"
    store = DictStore(str(path))
    client = ApiClient(app(OrchestrationService(store)))
    batch = client.post("/api/v1/projects/p/work-batches", headers=H, json={"title": "coord"})
    batch_id = batch.json()["batch"]["id"]
    routed = client.post(
        "/api/v1/projects/p/assignments",
        headers={**H, "Idempotency-Key": "asg"},
        json={"task_id": "t9", "agent_type": "frontend", "batch_id": batch_id},
    )
    assignment_id = routed.json()["assignment"]["id"]
    done = client.post(f"/api/v1/projects/p/assignments/{assignment_id}:complete", headers=H)
    assert done.json()["assignment"]["status"] == "completed"
    listed = client.get("/api/v1/projects/p/assignments", headers=H, params={"batch_id": batch_id})
    assert listed.json()["items"][0]["status"] == "completed"
    reloaded = DictStore(str(path))
    assert reloaded.get_assignment(assignment_id, Scope("t", "w", "p"))["status"] == "completed"
