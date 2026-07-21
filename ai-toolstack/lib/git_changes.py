"""Lightweight git change summary for ai-toolstack sync plan."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def git_change_stats(repo: Path) -> dict:
    proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return {"is_git_repo": False}

    lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
    modified = added = deleted = renamed = untracked = 0
    for ln in lines:
        xy = ln[:2]
        if xy == "??":
            untracked += 1
        elif xy[0] == "R" or xy[1] == "R":
            renamed += 1
        else:
            if xy[0] != " ":
                modified += 1
            if xy[1] != " ":
                if xy[1] == "D":
                    deleted += 1
                elif xy[1] == "A":
                    added += 1
                else:
                    modified += 1

    return {
        "is_git_repo": True,
        "total": len(lines),
        "modified": modified,
        "added": added,
        "deleted": deleted,
        "renamed": renamed,
        "untracked": untracked,
        "doc_changed": False,
        "code_changed": len(lines) > 0,
        "sync_scope_changed": False,
    }


def main() -> None:
    repo = Path(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--repo" else Path.cwd())
    if len(sys.argv) > 1 and sys.argv[1] == "git-changes":
        env_repo = __import__("os").environ.get("REPO_ROOT")
        if env_repo:
            repo = Path(env_repo)
    print(json.dumps(git_change_stats(repo.resolve())))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "git-changes":
        main()
    else:
        print(json.dumps(git_change_stats(Path.cwd())))
