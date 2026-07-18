from __future__ import annotations

from sdk import AgentCoreClient


def test_client_builds_url_and_headers():
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
