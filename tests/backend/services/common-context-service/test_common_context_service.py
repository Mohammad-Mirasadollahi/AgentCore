import asyncio

from httpx import ASGITransport, AsyncClient

from common_context_service.api import app
from common_context_service.core import CommonContextService
from common_context_service.testing import InMemoryStore


H = {"X-Tenant-Id": "t", "X-Workspace-Id": "w", "X-Actor-Id": "user", "Idempotency-Key": "one"}


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


def test_propose_approve_and_resolve_bundle():
    store = InMemoryStore()
    client = ApiClient(app(CommonContextService(store)))
    proposed = client.post(
        "/api/v1/projects/p/common-items",
        headers=H,
        json={"title": "Always use idempotency keys", "body": "All payment writes require Idempotency-Key.", "confidence": 0.9},
    )
    assert proposed.status_code == 200
    item_id = proposed.json()["item"]["id"]
    approved = client.post(f"/api/v1/projects/p/common-items/{item_id}:approve", headers=H)
    assert approved.json()["item"]["status"] == "approved"
    bundle = client.get("/api/v1/projects/p/common-context/bundle", headers=H, params={"token_budget": 800})
    assert bundle.json()["bundle"]["included"][0]["id"] == item_id
    assert store.outbox()[-1]["event_type"] == "common_item.approved"


def test_unapproved_items_omitted_from_bundle():
    client = ApiClient(app(CommonContextService(InMemoryStore())))
    client.post(
        "/api/v1/projects/p/common-items",
        headers=H,
        json={"title": "draft", "body": "not approved yet"},
    )
    bundle = client.get("/api/v1/projects/p/common-context/bundle", headers=H)
    assert bundle.json()["bundle"]["included"] == []


def test_title_and_body_required():
    client = ApiClient(app(CommonContextService(InMemoryStore())))
    bad = client.post("/api/v1/projects/p/common-items", headers=H, json={"title": "x", "body": ""})
    assert bad.status_code == 400


def test_suppress_and_reject_lifecycle(tmp_path):
    from common_context_service.core import Scope
    from common_context_service.testing import DictStore

    path = tmp_path / "common.json"
    store = DictStore(str(path))
    client = ApiClient(app(CommonContextService(store)))
    proposed = client.post(
        "/api/v1/projects/p/common-items",
        headers=H,
        json={"title": "Pin idempotency", "body": "Always send Idempotency-Key on writes."},
    )
    item_id = proposed.json()["item"]["id"]
    suppressed = client.post(
        f"/api/v1/projects/p/common-items/{item_id}:suppress",
        headers=H,
        json={"reason": "duplicates memory rule"},
    )
    assert suppressed.json()["item"]["status"] == "suppressed"
    rejected = client.post(
        "/api/v1/projects/p/common-items",
        headers={**H, "Idempotency-Key": "two"},
        json={"title": "noisy", "body": "ignore this"},
    )
    reject_id = rejected.json()["item"]["id"]
    denied = client.post(
        f"/api/v1/projects/p/common-items/{reject_id}:reject",
        headers=H,
        json={"reason": "too vague"},
    )
    assert denied.json()["item"]["status"] == "rejected"
    bundle = client.get("/api/v1/projects/p/common-context/bundle", headers=H)
    assert bundle.json()["bundle"]["included"] == []
    reloaded = DictStore(str(path))
    assert reloaded.get_item(item_id, Scope("t", "w", "p"))["status"] == "suppressed"
