"""Repository and ai-toolstack path helpers (Python counterpart of lib/paths.sh)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ToolstackPaths:
    repo: Path
    ai_toolstack: Path
    config: Path
    data: Path
    hooks: Path
    scripts: Path
    rules: Path
    docs: Path
    local: Path
    mcp_memory_dir: Path
    mcp_memory_file: Path
    legacy_mcp_memory: Path

    @classmethod
    def discover(cls, root: Path | None = None) -> ToolstackPaths:
        repo = (root or repo_root()).resolve()
        ai = repo / "ai-toolstack"
        data = ai / "data"
        return cls(
            repo=repo,
            ai_toolstack=ai,
            config=ai / "config",
            data=data,
            hooks=ai / "hooks",
            scripts=ai / "scripts",
            rules=ai / "rules",
            docs=ai / "docs",
            local=data / "local",
            mcp_memory_dir=data / "mcp-memory",
            mcp_memory_file=data / "mcp-memory" / "memory.jsonl",
            legacy_mcp_memory=repo / ".mcp-memory",
        )


def extend_tool_path() -> None:
    extra = [Path.home() / ".local/bin"]
    prefix = os.pathsep.join(str(p) for p in extra if p.is_dir())
    if prefix:
        os.environ["PATH"] = prefix + os.pathsep + os.environ.get("PATH", "")


def read_shell_export(env_file: Path, key: str, default: str = "") -> str:
    if not env_file.is_file():
        return default
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith(f"export {key}="):
            return stripped.split("=", 1)[1].strip().strip('"').strip("'")
        if stripped.startswith(f"{key}="):
            return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    return default
