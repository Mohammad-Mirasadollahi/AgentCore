"""Compatibility shim — prefer `agentcore_sdk`."""

from agentcore_sdk import AgentCoreClient, SdkError

__all__ = ["AgentCoreClient", "SdkError"]
