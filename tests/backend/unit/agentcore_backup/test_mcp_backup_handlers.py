"""Unit tests for MCP backup status/dry-run handlers."""

from __future__ import annotations

import json
from pathlib import Path

from agentcore_backup.bundle import pack_directory
from agentcore_backup.manifest import build_manifest, write_checksums
from agentcore_backup.scope import Scope
from mcp_gateway_service.backends import backup as backup_backend


def test_backup_status_and_dry_run(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AGENTCORE_ROOT", str(tmp_path))
    staging = tmp_path / "stg"
    staging.mkdir()
    manifest = build_manifest(
        scope=Scope("t", "w", "p"),
        contract_version="1",
        product_version="0.1.2",
        store_counts={"memory": 0},
        created_at="2026-08-01T00:00:00Z",
    )
    (staging / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    write_checksums(staging)
    acbak = tmp_path / "x.acbak"
    pack_directory(staging, acbak)

    base = {"maps_to": "backup.status"}
    status = backup_backend.backup_status(base=base)
    assert status["ok"] is True

    report = backup_backend.backup_dry_run(
        {"bundle_path": str(acbak), "replace": False},
        base={"maps_to": "backup.dry_run"},
    )
    assert report["ok"] is True
    assert report["action"] == "dry_run"
    assert report["would_fail_conflict"] is False
