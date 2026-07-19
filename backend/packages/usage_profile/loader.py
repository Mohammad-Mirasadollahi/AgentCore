from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


CATALOG_DIR = Path(__file__).resolve().parents[2] / "configs" / "usage-profiles"

REQUIRED_FIELDS = (
    "profile_id",
    "version",
    "title",
    "audience",
    "domain_pack",
    "feature_profile",
    "connectors",
    "mcp",
)

REQUIRED_TOOL_FIELDS = ("name", "description", "maps_to", "input_schema")


class UsageProfileError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise UsageProfileError(f"usage profile missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise UsageProfileError(f"usage profile must be an object: {path}")
    return data


def list_profile_ids(catalog_dir: Path | None = None) -> list[str]:
    root = catalog_dir or CATALOG_DIR
    if not root.is_dir():
        return []
    return sorted(path.stem for path in root.glob("*.json") if path.name != "README.md")


def load_usage_profile(profile_id: str, catalog_dir: Path | None = None) -> dict[str, Any]:
    profile_id = str(profile_id or "").strip()
    if not profile_id:
        raise UsageProfileError("profile_id is required")
    path = (catalog_dir or CATALOG_DIR) / f"{profile_id}.json"
    data = _load_json(path)
    if str(data.get("profile_id") or "") != profile_id:
        raise UsageProfileError(f"profile_id mismatch in {path.name}")
    errors = validate_usage_profile(data)
    if errors:
        raise UsageProfileError("; ".join(errors))
    return data


def validate_usage_profile(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in profile:
            errors.append(f"missing {field}")
    mcp = profile.get("mcp")
    if not isinstance(mcp, dict):
        errors.append("mcp object is required")
        return errors
    if not str(mcp.get("server_name") or "").strip():
        errors.append("mcp.server_name is required")
    tools = mcp.get("tools")
    if not isinstance(tools, list) or not tools:
        errors.append("mcp.tools must be a non-empty list")
        return errors
    seen: set[str] = set()
    for tool in tools:
        if not isinstance(tool, dict):
            errors.append("mcp tool must be an object")
            continue
        for field in REQUIRED_TOOL_FIELDS:
            if field not in tool or (field != "input_schema" and not str(tool.get(field) or "").strip()):
                errors.append(f"tool missing {field}")
        name = str(tool.get("name") or "").strip()
        if name:
            if name in seen:
                errors.append(f"duplicate tool name: {name}")
            seen.add(name)
        if not isinstance(tool.get("input_schema"), dict):
            errors.append(f"tool {name or '?'} input_schema must be an object")
    connectors = profile.get("connectors")
    if connectors is not None and not isinstance(connectors, list):
        errors.append("connectors must be a list")
    return errors


def resolve_effective_profile(
    profile_id: str,
    *,
    tenant_id: str,
    workspace_id: str,
    project_id: str,
    catalog_dir: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    catalog = load_usage_profile(profile_id, catalog_dir=catalog_dir)
    overrides = overrides or {}
    domain_pack = str(overrides.get("domain_pack") or catalog["domain_pack"])
    feature_profile = str(overrides.get("feature_profile") or catalog["feature_profile"])
    return {
        "profile_id": catalog["profile_id"],
        "version": catalog["version"],
        "title": catalog["title"],
        "audience": catalog["audience"],
        "domain_pack": domain_pack,
        "feature_profile": feature_profile,
        "connectors": list(catalog.get("connectors") or []),
        "mcp": catalog["mcp"],
        "defaults": dict(catalog.get("defaults") or {}),
        "scope": {
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "project_id": project_id,
        },
        "source": "usage_profile_catalog",
    }


def materialize_cursor_mcp_config(
    effective: dict[str, Any],
    *,
    python_executable: str = "python",
    module: str = "mcp_gateway_service",
    pythonpath: str | None = None,
) -> dict[str, Any]:
    mcp = effective.get("mcp") or {}
    server_name = str(mcp.get("server_name") or "agentcore")
    scope = effective.get("scope") or {}
    default_pythonpath = (
        "backend/services/mcp-gateway-service/src:"
        "backend/packages:"
        "backend/services/core-data-service/src:"
        "backend/services/memory-service/src:"
        "backend/services/code-graph-service/src:"
        "backend/services/docs-sync-service/src"
    )
    env = {
        "AGENTCORE_USAGE_PROFILE": str(effective.get("profile_id") or ""),
        "AGENTCORE_TENANT_ID": str(scope.get("tenant_id") or ""),
        "AGENTCORE_WORKSPACE_ID": str(scope.get("workspace_id") or ""),
        "AGENTCORE_PROJECT_ID": str(scope.get("project_id") or ""),
        "PYTHONPATH": pythonpath or default_pythonpath,
    }
    database_url = os.environ.get("AGENTCORE_DATABASE_URL", "").strip()
    if database_url:
        env["AGENTCORE_DATABASE_URL"] = database_url
        env["AGENTCORE_MCP_STORE_MODE"] = os.environ.get("AGENTCORE_MCP_STORE_MODE", "postgres")
    store_mode = os.environ.get("AGENTCORE_MCP_STORE_MODE", "").strip()
    if store_mode and "AGENTCORE_MCP_STORE_MODE" not in env:
        env["AGENTCORE_MCP_STORE_MODE"] = store_mode
    return {
        "mcpServers": {
            server_name: {
                "command": python_executable,
                "args": ["-m", module],
                "env": env,
            }
        }
    }
