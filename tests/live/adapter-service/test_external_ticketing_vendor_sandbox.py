"""Opt-in ExternalTicket vendor sandbox round-trip.

Requires explicit credentials. Skips cleanly in offline CI.
Covers create dispatch and optional remote status push.
"""

from __future__ import annotations

import os

import pytest

from adapter_service.core import AdapterService, Scope
from adapter_service.testing import InMemoryStore
from adapter_service.trackers import build_tracker_registry


def _vendor_env() -> str | None:
    if all(
        os.environ.get(key)
        for key in (
            "AGENTCORE_JIRA_BASE_URL",
            "AGENTCORE_JIRA_EMAIL",
            "AGENTCORE_JIRA_API_TOKEN",
            "AGENTCORE_JIRA_PROJECT_KEY",
        )
    ):
        return "jira"
    if all(os.environ.get(key) for key in ("AGENTCORE_LINEAR_API_KEY", "AGENTCORE_LINEAR_TEAM_ID")):
        return "linear"
    if all(os.environ.get(key) for key in ("AGENTCORE_GITHUB_TOKEN", "AGENTCORE_GITHUB_OWNER", "AGENTCORE_GITHUB_REPO")):
        return "github-issues"
    return None


VENDOR = _vendor_env()


@pytest.mark.live
@pytest.mark.skipif(VENDOR is None, reason="no vendor sandbox credentials configured")
def test_external_ticket_vendor_sandbox_create_and_status_round_trip():
    assert VENDOR is not None
    registry = build_tracker_registry()
    assert VENDOR in registry
    store = InMemoryStore()
    service = AdapterService(store, tracker_adapters=registry)
    scope = Scope("sandbox", "agentcore", "ticket-vendor-sandbox")
    connector = service.register_connector(
        scope,
        "sandbox-ops",
        "vendor-sandbox",
        f"sandbox-reg-{VENDOR}",
        {
            "vendor": VENDOR,
            "name": f"{VENDOR}-sandbox",
            "capabilities": ["tickets"],
            "auth_profile": "token",
            "credential": "sandbox",
            "status_map": {"Done": "done", "Closed": "done"},
        },
    )
    service.validate_connector(scope, "sandbox-ops", "vendor-sandbox", f"sandbox-val-{VENDOR}", connector.id)
    ticket = service.create_external_ticket(
        scope,
        "sandbox-ops",
        "vendor-sandbox",
        f"sandbox-create-{VENDOR}",
        {
            "connector_id": connector.id,
            "title": f"AgentCore sandbox {VENDOR}",
            "department": "platform-engineering",
            "description_summary": "Opt-in ExternalTicket vendor sandbox create",
            "extension": (
                {"linear_state_id": os.environ["AGENTCORE_LINEAR_DONE_STATE_ID"]}
                if VENDOR == "linear" and os.environ.get("AGENTCORE_LINEAR_DONE_STATE_ID")
                else {}
            ),
        },
    )
    dispatched = service.dispatch_external_ticket(
        scope,
        "sandbox-ops",
        "vendor-sandbox",
        f"sandbox-dispatch-{VENDOR}",
        ticket.id,
    )
    assert dispatched.dispatch_status.value == "succeeded"
    assert dispatched.external_ref

    if VENDOR == "linear" and not os.environ.get("AGENTCORE_LINEAR_DONE_STATE_ID"):
        pytest.skip("linear status push requires AGENTCORE_LINEAR_DONE_STATE_ID")

    pushed = service.push_external_ticket_status(
        scope,
        "sandbox-ops",
        "vendor-sandbox",
        f"sandbox-push-{VENDOR}",
        dispatched.id,
        dispatched.version,
        "done",
    )
    assert pushed.dispatch_status.value == "succeeded"
    assert pushed.status.value == "done"
    assert pushed.external_updated_at
