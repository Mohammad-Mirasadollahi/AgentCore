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


def _approve(service, scope, payload, key):
    item = service.propose_item(scope, "user", "c", key, payload)
    return service.approve_item(scope, item["id"], "user")


def test_org_agents_entry_fallback_when_project_empty():
    from common_context_service.core import org_scope, project_scope

    service = CommonContextService(InMemoryStore())
    org = org_scope("t", "w")
    _approve(
        service,
        org,
        {"item_type": "agents_entry", "title": "Org entry", "body": "# Org"},
        "org-entry",
    )
    bundle = service.resolve_guidance(project_scope("t", "w", "p"), user_id="user")
    assert bundle["agents_entry"]["body"] == "# Org"
    assert bundle["agents_entry"]["layer"] == "org"
    assert bundle["layers_considered"] == ["org", "project", "user"]


def test_project_overrides_org_same_slug_rule():
    from common_context_service.core import org_scope, project_scope

    service = CommonContextService(InMemoryStore())
    org = org_scope("t", "w")
    proj = project_scope("t", "w", "p")
    _approve(
        service,
        org,
        {
            "item_type": "always_rule",
            "title": "Org rule",
            "body": "org body",
            "slug": "shared-rule",
            "mandatory": False,
        },
        "org-rule",
    )
    _approve(
        service,
        proj,
        {
            "item_type": "always_rule",
            "title": "Project rule",
            "body": "project body",
            "slug": "shared-rule",
            "mandatory": False,
        },
        "proj-rule",
    )
    bundle = service.resolve_guidance(proj, user_id="user")
    rules = [r for r in bundle["always_rules"] if r.get("slug") == "shared-rule"]
    assert len(rules) == 1
    assert rules[0]["body"] == "project body"
    assert rules[0]["layer"] == "project"


def test_user_overrides_non_mandatory_project_rule():
    from common_context_service.core import project_scope, user_scope

    service = CommonContextService(InMemoryStore())
    proj = project_scope("t", "w", "p")
    user = user_scope("t", "w", "alice")
    _approve(
        service,
        proj,
        {
            "item_type": "always_rule",
            "title": "Project style",
            "body": "project style",
            "slug": "style",
            "mandatory": False,
        },
        "proj-style",
    )
    _approve(
        service,
        user,
        {
            "item_type": "always_rule",
            "title": "User style",
            "body": "user style",
            "slug": "style",
            "mandatory": False,
        },
        "user-style",
    )
    bundle = service.resolve_guidance(proj, user_id="alice")
    rules = [r for r in bundle["always_rules"] if r.get("slug") == "style"]
    assert len(rules) == 1
    assert rules[0]["body"] == "user style"
    assert rules[0]["layer"] == "user"


def test_user_cannot_override_mandatory_project_rule():
    from common_context_service.core import project_scope, user_scope

    service = CommonContextService(InMemoryStore())
    proj = project_scope("t", "w", "p")
    user = user_scope("t", "w", "alice")
    _approve(
        service,
        proj,
        {
            "item_type": "always_rule",
            "title": "Mandatory",
            "body": "must follow",
            "slug": "law",
            "mandatory": True,
        },
        "proj-law",
    )
    _approve(
        service,
        user,
        {
            "item_type": "always_rule",
            "title": "User try",
            "body": "user rewrite",
            "slug": "law",
            "mandatory": False,
        },
        "user-law",
    )
    bundle = service.resolve_guidance(proj, user_id="alice")
    rules = [r for r in bundle["always_rules"] if r.get("slug") == "law"]
    assert len(rules) == 1
    assert rules[0]["body"] == "must follow"
    assert rules[0]["layer"] == "project"
    assert any(c["reason_code"] == "mandatory_override_blocked" for c in bundle["conflicts"])


def test_user_cannot_propose_agents_entry():
    from common_context_service.core import ValidationError, user_scope

    service = CommonContextService(InMemoryStore())
    user = user_scope("t", "w", "alice")
    try:
        service.propose_item(
            user,
            "alice",
            "c",
            "bad-entry",
            {"item_type": "agents_entry", "title": "Nope", "body": "# no"},
        )
        assert False, "expected validation error"
    except ValidationError as exc:
        assert "agents_entry" in str(exc)


def test_user_cannot_propose_mandatory_rule():
    from common_context_service.core import ValidationError, user_scope

    service = CommonContextService(InMemoryStore())
    user = user_scope("t", "w", "alice")
    try:
        service.propose_item(
            user,
            "alice",
            "c",
            "bad-mand",
            {
                "item_type": "always_rule",
                "title": "Nope",
                "body": "x",
                "slug": "x",
                "mandatory": True,
            },
        )
        assert False, "expected validation error"
    except ValidationError as exc:
        assert "mandatory" in str(exc)


def test_list_and_get_skill_merged_catalog():
    from common_context_service.core import org_scope, project_scope, user_scope

    service = CommonContextService(InMemoryStore())
    org = org_scope("t", "w")
    proj = project_scope("t", "w", "p")
    user = user_scope("t", "w", "alice")
    _approve(
        service,
        org,
        {
            "item_type": "skill",
            "name": "shared-skill",
            "title": "Org skill",
            "body": "org skill body",
            "description": "from org",
        },
        "org-skill",
    )
    _approve(
        service,
        proj,
        {
            "item_type": "skill",
            "name": "project-only",
            "title": "Project skill",
            "body": "project skill body",
            "description": "from project",
        },
        "proj-skill",
    )
    _approve(
        service,
        user,
        {
            "item_type": "skill",
            "name": "shared-skill",
            "title": "User skill",
            "body": "user skill body",
            "description": "from user",
        },
        "user-skill",
    )
    catalog = service.list_skills(proj, user_id="alice")
    by_name = {s["name"]: s for s in catalog}
    assert by_name["shared-skill"]["layer"] == "user"
    assert by_name["project-only"]["layer"] == "project"
    fetched = service.get_skill(proj, name="shared-skill", user_id="alice")
    assert fetched["body"] == "user skill body"
    assert fetched["layer"] == "user"


def test_backward_compat_omit_scope_kind_is_project():
    service = CommonContextService(InMemoryStore())
    scope = Scope("t", "w", "p")
    assert scope.scope_kind == "project"
    item = service.propose_item(
        scope,
        "user",
        "c",
        "compat-1",
        {"item_type": "skill", "name": "compat", "title": "c", "body": "body"},
    )
    service.approve_item(scope, item["id"], "user")
    bundle = service.resolve_guidance(scope)
    assert any(s["name"] == "compat" and s["layer"] == "project" for s in bundle["skills"])
    assert "org" in bundle["layers_considered"]
    assert "project" in bundle["layers_considered"]


def test_api_propose_org_and_user_layers():
    store = InMemoryStore()
    client = ApiClient(app(CommonContextService(store)))
    org_item = client.post(
        "/api/v1/projects/p/common-items",
        headers={**H, "Idempotency-Key": "org-1"},
        json={
            "scope_kind": "org",
            "item_type": "agents_entry",
            "title": "Org",
            "body": "# Org via API",
        },
    )
    assert org_item.status_code == 200
    org_id = org_item.json()["item"]["id"]
    assert org_item.json()["item"]["scope_kind"] == "org"
    approved = client.post(
        f"/api/v1/projects/p/common-items/{org_id}:approve",
        headers=H,
        json={"scope_kind": "org"},
    )
    assert approved.status_code == 200

    user_item = client.post(
        "/api/v1/projects/p/common-items",
        headers={**H, "Idempotency-Key": "user-1", "X-Actor-Id": "alice"},
        json={
            "scope_kind": "user",
            "item_type": "skill",
            "name": "my-skill",
            "title": "Mine",
            "body": "personal skill",
        },
    )
    assert user_item.status_code == 200
    user_id = user_item.json()["item"]["id"]
    client.post(
        f"/api/v1/projects/p/common-items/{user_id}:approve",
        headers={**H, "X-Actor-Id": "alice"},
        json={"scope_kind": "user", "user_id": "alice"},
    )

    resolved = client.post(
        "/api/v1/projects/p/guidance/resolve",
        headers={**H, "X-Actor-Id": "alice"},
        json={},
    )
    assert resolved.status_code == 200
    bundle = resolved.json()["bundle"]
    assert bundle["agents_entry"]["layer"] == "org"
    assert any(s["name"] == "my-skill" and s["layer"] == "user" for s in bundle["skills"])


def test_task_overrides_suppress_non_mandatory_and_block_mandatory():
    from common_context_service.core import project_scope

    service = CommonContextService(InMemoryStore())
    proj = project_scope("t", "w", "p")
    _approve(
        service,
        proj,
        {
            "item_type": "always_rule",
            "title": "Soft",
            "body": "soft rule",
            "slug": "soft-rule",
            "mandatory": False,
        },
        "soft",
    )
    _approve(
        service,
        proj,
        {
            "item_type": "always_rule",
            "title": "Hard",
            "body": "hard rule",
            "slug": "hard-rule",
            "mandatory": True,
        },
        "hard",
    )
    _approve(
        service,
        proj,
        {
            "item_type": "skill",
            "name": "skip-me",
            "title": "Skip",
            "body": "skill body",
            "description": "skip",
        },
        "skill-skip",
    )
    bundle = service.resolve_guidance(
        proj,
        user_id="alice",
        task_overrides={
            "suppress_rule_slugs": ["soft-rule", "hard-rule"],
            "suppress_skill_names": ["skip-me"],
        },
    )
    slugs = {r.get("slug") for r in bundle["always_rules"]}
    assert "soft-rule" not in slugs
    assert "hard-rule" in slugs
    assert all(s["name"] != "skip-me" for s in bundle["skills"])
    assert any(c["reason_code"] == "task_override_blocked" for c in bundle["conflicts"])
    assert any(s["reason_code"] == "task_override" for s in bundle["suppressed_items"])


def test_org_mcp_first_seed_idempotent():
    from common_context_service.core import org_scope, project_scope

    service = CommonContextService(InMemoryStore())
    org = org_scope("t", "w")
    first = service.ensure_mcp_first_seed(org, "ops", "corr-org")
    assert first["seeded"] is True
    assert first["scope_kind"] == "org"
    second = service.ensure_mcp_first_seed(org, "ops", "corr-org-2")
    assert second["seeded"] is False
    bundle = service.resolve_guidance(project_scope("t", "w", "p"), user_id="alice")
    assert bundle["agents_entry"] is not None
    assert bundle["agents_entry"]["layer"] == "org"
    assert any(r.get("slug") == "mcp-first-agentcore" for r in bundle["always_rules"])
