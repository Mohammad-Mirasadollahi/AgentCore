from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def default_state_root(repo_root: Path) -> Path:
    return repo_root / ".agentcore" / "projects"


def project_path(root: Path, tenant_id: str, workspace_id: str, project_id: str) -> Path:
    return root / tenant_id / workspace_id / f"{project_id}.json"


def load_project(root: Path, tenant_id: str, workspace_id: str, project_id: str) -> dict[str, Any] | None:
    path = project_path(root, tenant_id, workspace_id, project_id)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid project state: {path}")
    return data


def save_project(root: Path, project: dict[str, Any]) -> Path:
    path = project_path(
        root,
        str(project["tenant_id"]),
        str(project["workspace_id"]),
        str(project["project_id"]),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
