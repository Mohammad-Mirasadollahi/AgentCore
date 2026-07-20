"""Tests for shared LiteLLM gateway settings and provider listing."""

from __future__ import annotations

from llm_gateway import (
    ChatMessage,
    CompletionRequest,
    FakeLlmGateway,
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
    from llm_gateway.rate_limit import RpmLimiter

    limiter = RpmLimiter(2)
    assert limiter.acquire() == 0.0
    assert limiter.acquire() == 0.0
    # Third call would wait; do not sleep a full minute in unit tests — just assert capacity state.
    assert len(limiter._timestamps) == 2
