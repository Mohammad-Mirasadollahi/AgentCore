"""Code-graph operator CLI commands."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from agentcore_cli.util import now_iso, print_json, repo_root, require_scope


def _ensure_code_graph_import() -> None:
    root = repo_root()
    src = root / "backend" / "services" / "code-graph-service" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _graph_service():
    """In-process code-graph service (auto neo4j when password set; else memory)."""
    from agentcore_cli.cli_defaults import load_dotenv_files

    load_dotenv_files()
    _ensure_code_graph_import()
    backend = os.environ.get("AGENTCORE_GRAPH_CLI_BACKEND", "").strip().lower()
    if not backend:
        pwd = os.environ.get("AGENTCORE_NEO4J_PASSWORD", "").strip()
        backend = "neo4j" if pwd and pwd not in {
            "replace-with-a-local-secret",
            "changeme",
            "password",
            "neo4j",
        } else "memory"
    if backend == "neo4j":
        try:
            from agentcore_cli.remote_client import apply_compose_env_to_os

            apply_compose_env_to_os(os.environ, repo_root())
        except SystemExit:
            pass
        from code_graph_service.bootstrap import Settings, build_service

        return build_service(Settings.from_environment())
    from code_graph_service.core import CodeGraphService
    from code_graph_service.testing import InMemoryStore

    return CodeGraphService(InMemoryStore())


def _graph_scope(args: argparse.Namespace, *, with_defaults: bool = False):
    _ensure_code_graph_import()
    from code_graph_service.core import Scope

    tenant, workspace, project = require_scope(args, with_defaults=with_defaults)
    return Scope(tenant, workspace, project)


def cmd_graph_ingest(args: argparse.Namespace) -> int:
    svc = _graph_service()
    scope = _graph_scope(args)
    root_path = Path(args.path).resolve()
    if not root_path.is_dir():
        raise SystemExit(f"error: path is not a directory: {root_path}")
    result = svc.ingest_repo(
        scope,
        "cli",
        f"cli-{now_iso()}",
        f"cli-repo:{root_path}",
        {
            "root_path": str(root_path),
            "include_extensions": [".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"],
            "max_files": int(args.max_files),
            "include_outcomes": True,
        },
    )
    payload = result.to_dict() if hasattr(result, "to_dict") else result
    print_json({"ok": True, "path": str(root_path), "result": payload})
    return 0


def cmd_graph_freshness(args: argparse.Namespace) -> int:
    svc = _graph_service()
    _graph_scope(args)
    if args.mark_pending:
        svc.mark_file_pending(args.mark_pending)
    print_json(svc.freshness_status())
    return 0


def cmd_graph_explore(args: argparse.Namespace) -> int:
    svc = _graph_service()
    scope = _graph_scope(args)
    pack = svc.explore(scope, args.query, top_k=int(args.top_k))
    print_json(pack)
    return 0


def cmd_graph_hybrid(args: argparse.Namespace) -> int:
    svc = _graph_service()
    scope = _graph_scope(args)
    print_json(svc.hybrid_search(scope, args.query, top_k=int(args.top_k)))
    return 0


def cmd_graph_smoke(args: argparse.Namespace) -> int:
    """One-shot connect proxy: ingest → freshness → hybrid → explore (same process)."""
    svc = _graph_service()
    scope = _graph_scope(args)
    root_path = Path(args.path).resolve()
    if not root_path.is_dir():
        raise SystemExit(f"error: path is not a directory: {root_path}")
    ingest = svc.ingest_repo(
        scope,
        "cli-smoke",
        f"smoke-{now_iso()}",
        f"smoke-repo:{root_path}",
        {
            "root_path": str(root_path),
            "include_extensions": [".py"],
            "max_files": int(args.max_files),
            "include_outcomes": True,
        },
    )
    ingest_payload = ingest.to_dict() if hasattr(ingest, "to_dict") else ingest
    fresh = svc.freshness_status()
    hybrid = svc.hybrid_search(scope, args.query, top_k=5)
    explore = svc.explore(scope, args.query, top_k=8)
    report = {
        "ok": bool(hybrid.get("hits")) and bool(explore.get("sections")),
        "ingest": ingest_payload,
        "freshness": fresh,
        "hybrid_hits": len(hybrid.get("hits") or []),
        "embedding_backend": hybrid.get("embedding_backend"),
        "explore_sections": len(explore.get("sections") or []),
        "query": args.query,
    }
    print_json(report)
    return 0 if report["ok"] else 1


def cmd_graph_watch(args: argparse.Namespace) -> int:
    """Poll filesystem and batch pending-sync (debounce; never per keystroke)."""
    script = (
        repo_root()
        / "backend"
        / "services"
        / "code-graph-service"
        / "scripts"
        / "watch_pending_sync.py"
    )
    if not script.is_file():
        raise SystemExit(f"error: watcher script missing: {script}")
    cmd = [
        sys.executable,
        str(script),
        "--path",
        str(Path(args.path).resolve()),
        "--interval",
        str(args.interval),
        "--debounce",
        str(args.debounce),
        "--max-wait",
        str(args.max_wait),
    ]
    if args.once:
        cmd.append("--once")
    env = os.environ.copy()
    env.setdefault("AGENTCORE_TENANT_ID", str(args.tenant))
    env.setdefault("AGENTCORE_WORKSPACE_ID", str(args.workspace))
    env.setdefault("AGENTCORE_PROJECT_ID", str(args.project))
    return subprocess.call(cmd, env=env, cwd=str(repo_root()))
