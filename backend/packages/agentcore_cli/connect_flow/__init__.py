"""Connect orchestration package (HTTP preferred, SSH fallback).

Public entrypoints stay importable as ``agentcore_cli.connect_flow``.
"""

from agentcore_cli.connect_flow.api import api_bootstrap, api_health, api_ingest, mcp_http_smoke
from agentcore_cli.connect_flow.ingest import remote_ingest
from agentcore_cli.connect_flow.remote_purge import remote_purge_from_args
from agentcore_cli.connect_flow.remote_sync import (
    _client_remote_cloud_llm_allowed,
    _remote_llm_config,
    remote_sync_from_args,
)
from agentcore_cli.connect_flow.run import reachability_check, run_connect
from agentcore_cli.connect_flow.ssh import _remote_is_dir, _run_ssh

__all__ = [
    "_client_remote_cloud_llm_allowed",
    "_remote_is_dir",
    "_remote_llm_config",
    "_run_ssh",
    "api_bootstrap",
    "api_health",
    "api_ingest",
    "mcp_http_smoke",
    "reachability_check",
    "remote_ingest",
    "remote_purge_from_args",
    "remote_sync_from_args",
    "run_connect",
]
