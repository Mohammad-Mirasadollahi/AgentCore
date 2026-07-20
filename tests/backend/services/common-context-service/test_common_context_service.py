import asyncio

from httpx import ASGITransport, AsyncClient

from common_context_service.api import app
from common_context_service.core import CommonContextService, ConflictError, Scope
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


def test_guidance_resolve_seed_and_get_skill():
    store = InMemoryStore()
    client = ApiClient(app(CommonContextService(store)))
    seeded = client.post("/api/v1/projects/p/guidance/seed-mcp-first", headers=H)
    assert seeded.status_code == 200
    assert seeded.json()["seeded"] is True
    assert len(seeded.json()["item_ids"]) >= 8

    again = client.post("/api/v1/projects/p/guidance/seed-mcp-first", headers=H)
    assert again.json()["seeded"] is False

    resolved = client.post(
        "/api/v1/projects/p/guidance/resolve",
        headers=H,
        json={"task_summary": "start coding session"},
    )
    assert resolved.status_code == 200
    bundle = resolved.json()["bundle"]
    assert bundle["agents_entry"] is not None
    assert bundle["agents_entry"]["body"].startswith("# Agent entry")
    assert any(r.get("slug") == "mcp-first-agentcore" for r in bundle["always_rules"])
    assert any(s["name"] == "agentcore-memory" for s in bundle["skills"])
    assert all("body" not in s for s in bundle["skills"])

    skills = client.get("/api/v1/projects/p/guidance/skills", headers=H, params={"query": "memory"})
    assert any(s["name"] == "agentcore-memory" for s in skills.json()["skills"])

    fetched = client.post(
        "/api/v1/projects/p/guidance/skills:get",
        headers=H,
        json={"name": "agentcore-memory", "bundle_id": bundle["bundle_id"]},
    )
    assert fetched.status_code == 200
    assert "agentcore_memory_retrieve" in fetched.json()["skill"]["body"]

    export = client.post(
        "/api/v1/projects/p/guidance/export",
        headers=H,
        json={"layout": "cursor", "dry_run": True},
    )
    paths = {p["path"] for p in export.json()["export"]["planned"]}
    assert "AGENTS.md" in paths
    assert any(p.startswith(".cursor/rules/") for p in paths)
    assert any(p.startswith(".cursor/skills/") for p in paths)


def test_single_agents_entry_invariant():
    service = CommonContextService(InMemoryStore())
    scope = Scope("t", "w", "p")
    first = service.propose_item(
        scope,
        "user",
        "c1",
        "entry-1",
        {"item_type": "agents_entry", "title": "Entry A", "body": "# A"},
    )
    service.approve_item(scope, first["id"], "user")
    second = service.propose_item(
        scope,
        "user",
        "c2",
        "entry-2",
        {"item_type": "agents_entry", "title": "Entry B", "body": "# B"},
    )
    try:
        service.approve_item(scope, second["id"], "user")
        assert False, "expected conflict"
    except ConflictError:
        pass


def test_skill_requires_name():
    client = ApiClient(app(CommonContextService(InMemoryStore())))
    bad = client.post(
        "/api/v1/projects/p/common-items",
        headers=H,
        json={"item_type": "skill", "title": "x", "body": "y"},
    )
    assert bad.status_code == 400
