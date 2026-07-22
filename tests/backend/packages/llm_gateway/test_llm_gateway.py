"""Tests for shared LiteLLM gateway settings and provider listing."""

from __future__ import annotations

import sys

import pytest

from llm_gateway import (
    ChatMessage,
    CompletionRequest,
    FakeLlmGateway,
    LiteLlmGateway,
    LlmGatewaySettings,
    list_providers,
    resolve_api_base,
)
from llm_gateway.settings import DEFAULT_NUM_RETRIES, DEFAULT_RPM, DEFAULT_TIMEOUT_SECONDS


def test_resolve_api_base_auto():
    assert resolve_api_base(override=None, host="127.0.0.1", port=32400) == "http://127.0.0.1:32400"
    assert resolve_api_base(override="", host="127.0.0.1", port=32400) == "http://127.0.0.1:32400"


def test_resolve_api_base_override_wins():
    assert (
        resolve_api_base(override="http://proxy.example:9999/", host="127.0.0.1", port=32400)
        == "http://proxy.example:9999"
    )


def test_settings_defaults_timeout_retries_and_rpm(monkeypatch):
    monkeypatch.delenv("AGENTCORE_LITELLM_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("AGENTCORE_LITELLM_NUM_RETRIES", raising=False)
    monkeypatch.delenv("AGENTCORE_LITELLM_RPM", raising=False)
    monkeypatch.delenv("AGENTCORE_LITELLM_API_BASE", raising=False)
    monkeypatch.delenv("LITELLM_API_BASE", raising=False)
    monkeypatch.setenv("AGENTCORE_LITELLM_PORT", "32400")
    settings = LlmGatewaySettings.from_environment()
    assert settings.timeout_seconds == DEFAULT_TIMEOUT_SECONDS
    assert settings.num_retries == DEFAULT_NUM_RETRIES
    assert settings.rpm == DEFAULT_RPM
    assert settings.api_base_is_auto is True
    assert settings.api_base == "http://127.0.0.1:32400"


def test_settings_override_base_url(monkeypatch):
    monkeypatch.setenv("AGENTCORE_LITELLM_API_BASE", "http://10.0.0.5:4100")
    monkeypatch.setenv("AGENTCORE_LITELLM_TIMEOUT_SECONDS", "90")
    monkeypatch.setenv("AGENTCORE_LITELLM_NUM_RETRIES", "5")
    monkeypatch.setenv("AGENTCORE_LITELLM_RPM", "60")
    settings = LlmGatewaySettings.from_environment()
    assert settings.api_base == "http://10.0.0.5:4100"
    assert settings.api_base_is_auto is False
    assert settings.timeout_seconds == 90.0
    assert settings.num_retries == 5
    assert settings.rpm == 60


def test_list_providers_marks_configured_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    providers = {p.id: p for p in list_providers(include_litellm_dynamic=False)}
    assert providers["openai"].configured is True
    assert providers["anthropic"].configured is False


def test_fake_gateway_complete_and_providers():
    gateway = FakeLlmGateway(canned="hello")
    result = gateway.complete(
        CompletionRequest(messages=(ChatMessage(role="user", content="hi"),), model="fake/model")
    )
    assert result.content == "hello"
    assert gateway.list_providers()
    pub = gateway.settings_public()
    assert pub["timeout_seconds"] == 180.0
    assert pub["num_retries"] == 3
    assert pub["rpm"] == 30
    assert pub["reasoning_enabled"] is False
    assert "api_key" not in pub


def test_reasoning_payload_and_settings(monkeypatch):
    from llm_gateway import build_reasoning_payload

    assert build_reasoning_payload(enabled=False) is None
    assert build_reasoning_payload(enabled=True) == {"enabled": True}
    assert build_reasoning_payload(enabled=True, effort="high") == {
        "enabled": True,
        "effort": "high",
    }

    monkeypatch.setenv("AGENTCORE_LITELLM_PORT", "32400")
    monkeypatch.setenv("AGENTCORE_LITELLM_REASONING_ENABLED", "true")
    monkeypatch.setenv("AGENTCORE_LITELLM_REASONING_EFFORT", "medium")
    settings = LlmGatewaySettings.from_environment()
    assert settings.reasoning_enabled is True
    assert settings.reasoning_effort == "medium"
    assert settings.reasoning_payload() == {"enabled": True, "effort": "medium"}
    assert settings.reasoning_payload(enabled_override=False) is None
    assert settings.reasoning_payload(enabled_override=True, effort_override="") == {
        "enabled": True
    }


def test_rpm_limiter_allows_burst_then_blocks():
    from llm_gateway.rate_limit import RpmSessionGate

    gate = RpmSessionGate(2)
    s1 = gate.acquire("complete")
    s2 = gate.acquire("complete")
    snap = gate.snapshot()
    assert snap["starts_in_window"] == 2
    assert snap["inflight_count"] == 2
    gate.release(s1, "ok")
    gate.release(s2, "ok")
    snap2 = gate.snapshot()
    assert snap2["inflight_count"] == 0
    assert len(snap2["history"]) == 2


def test_rpm_session_release_on_error_and_history_cap():
    from llm_gateway.rate_limit import RpmSessionGate

    gate = RpmSessionGate(5, history_size=3)
    sessions = [gate.acquire("complete") for _ in range(3)]
    for s in sessions:
        gate.release(s, "error", error_detail="boom")
    extra = gate.acquire("embed")
    gate.release(extra, "ok")
    snap = gate.snapshot()
    assert snap["inflight_count"] == 0
    assert len(snap["history"]) == 3
    assert all(h["status"] in {"ok", "error"} for h in snap["history"])


def test_rpm_inflight_cap_blocks_until_release():
    import threading

    from llm_gateway.rate_limit import RpmSessionGate

    clock = {"t": 1000.0}

    def mono() -> float:
        return clock["t"]

    gate = RpmSessionGate(10, inflight_cap=1, clock=mono)
    first = gate.acquire("complete")
    got: list = []

    def other() -> None:
        got.append(gate.acquire("complete"))

    t = threading.Thread(target=other, daemon=True)
    t.start()
    t.join(timeout=0.2)
    assert t.is_alive()
    assert got == []
    gate.release(first, "ok")
    t.join(timeout=1.0)
    assert not t.is_alive()
    assert len(got) == 1
    gate.release(got[0], "ok")


def test_fake_gateway_releases_rpm_session():
    gateway = FakeLlmGateway(canned="hello")
    gateway.complete(
        CompletionRequest(messages=(ChatMessage(role="user", content="hi"),), model="fake/model")
    )
    snap = gateway.rpm_sessions_snapshot()
    assert snap["inflight_count"] == 0
    assert snap["starts_in_window"] == 1
    assert snap["history"][0]["status"] == "ok"


def test_litellm_gateway_releases_sessions_on_failures(monkeypatch):
    class FailingLiteLlm:
        drop_params = False

        @staticmethod
        def completion(**_kwargs):
            raise TimeoutError("provider timed out with sk-secret-value")

        @staticmethod
        def embedding(**_kwargs):
            raise RuntimeError("provider failed")

    monkeypatch.setitem(sys.modules, "litellm", FailingLiteLlm())
    gateway = LiteLlmGateway(settings=FakeLlmGateway().settings)

    with pytest.raises(TimeoutError):
        gateway.complete(
            CompletionRequest(
                messages=(ChatMessage(role="user", content="hi"),),
                model="fake/model",
            )
        )
    with pytest.raises(RuntimeError, match="provider failed"):
        gateway.embed("hello", model="fake/embed")

    snap = gateway.rpm_sessions_snapshot()
    assert snap["inflight_count"] == 0
    assert [item["status"] for item in snap["history"][:2]] == ["error", "cancelled"]
    assert [item["error_detail"] for item in snap["history"][:2]] == [
        "RuntimeError",
        "TimeoutError",
    ]
    assert "sk-secret-value" not in str(snap)
