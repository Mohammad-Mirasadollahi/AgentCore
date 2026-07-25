"""GAP-T06: agentcore_sdk client unit tests (parity with sdk package)."""

from __future__ import annotations

import httpx
import pytest

from agentcore_sdk import AgentCoreClient, SdkError


def test_agentcore_sdk_requires_base_url():
    with pytest.raises(SdkError):
        AgentCoreClient("")


def test_agentcore_sdk_builds_url_and_headers():
    client = AgentCoreClient(
        "http://127.0.0.1:32100",
        default_headers={"X-Tenant-Id": "t"},
    )
    request = client.build_request(
        "POST",
        "/projects/p/tasks",
        correlation_id="corr_1",
        idempotency_key="idem_1",
    )
    assert request["method"] == "POST"
    assert request["url"] == "http://127.0.0.1:32100/api/v1/projects/p/tasks"
    assert request["headers"]["X-Tenant-Id"] == "t"
    assert request["headers"]["X-Correlation-Id"] == "corr_1"
    assert request["headers"]["Idempotency-Key"] == "idem_1"


def test_agentcore_sdk_http_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(201, json={"id": "task_1"})

    client = AgentCoreClient(
        "http://127.0.0.1:32100",
        default_headers={"X-Tenant-Id": "t"},
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    assert client.get("/projects/p", correlation_id="c1").json() == {"ok": True}
    assert (
        client.post(
            "/projects/p/tasks",
            json={"title": "x"},
            correlation_id="c2",
            idempotency_key="i1",
        ).json()["id"]
        == "task_1"
    )


def test_generated_operations_stub_nonempty():
    from sdk.generated import OPERATIONS

    assert isinstance(OPERATIONS, list)
    assert OPERATIONS
    assert {op["operation_id"] for op in OPERATIONS} >= {
        "getHealth",
        "createTask",
        "listTasks",
    }
