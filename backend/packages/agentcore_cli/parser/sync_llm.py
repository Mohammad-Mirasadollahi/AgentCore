"""``connect``, ``sync``, ``llm``, ``purge``."""

from __future__ import annotations

import argparse

from agentcore_cli.parser._core import DEFAULT_SYNC_MAX_FILES
from agentcore_cli.util import add_scope_args


def register(sub: argparse._SubParsersAction) -> None:
    connect = sub.add_parser(
        "connect",
        help="One-command coding-agent onboarding (interactive SSH wizard or connect.yaml)",
    )
    connect.add_argument(
        "connect_mode",
        nargs="?",
        default="",
        metavar="edit|init|PATH[,PATH…]",
        help=(
            "Optional: edit (re-auth SSH), init (connect.yaml template), "
            "or one/more project dirs comma-separated (default: cwd). "
            "Each dir is wired for MCP and pinned for sync."
        ),
    )
    connect.add_argument("--config", default="", help="Path to connect.yaml / connect.json")
    connect.add_argument("--project", default="", help="Override project id (default: cwd directory name)")
    connect.add_argument("--ssh", default="", help="Override server.ssh")
    connect.add_argument("--server", default="", help="Override server.url (API bootstrap)")
    connect.add_argument("--clients", default="", help="Override clients (all or comma-separated ids)")
    connect.add_argument(
        "--include-user-clients",
        action="store_true",
        help="Also write user-global MCP configs",
    )
    connect.add_argument("--dry-run", action="store_true", help="Print MCP fragment only")
    connect.add_argument(
        "--local",
        action="store_true",
        help="Same-host stdio MCP (dogfood this checkout; no SSH/HTTP required)",
    )
    connect.add_argument("--tenant", default="", help="Override scope.tenant (local mode)")
    connect.add_argument("--workspace", default="", help="Override scope.workspace (local mode)")
    connect.add_argument(
        "--usage-profile",
        default="",
        help="Usage Profile id (chosen at connect; required if not in connect.yaml / non-interactive)",
    )
    connect.add_argument(
        "--remote-root",
        default="",
        help="AgentCore checkout root (local mode; default: detected repo root / cwd)",
    )

    sync = sub.add_parser(
        "sync",
        help="Sync code into the project graph (auto full vs incremental)",
    )
    add_scope_args(sync, required=False)
    sync.add_argument(
        "--path",
        action="append",
        default=None,
        help="Override: sync only these roots (repeatable). Default: paths from init / paths list",
    )
    sync.set_defaults(max_files=DEFAULT_SYNC_MAX_FILES)
    sync.epilog = "Limit file count with bare: max-file <n>  (example: agentcore sync max-file 50)"
    sync.add_argument(
        "--cpu-percent",
        default=None,
        metavar="N",
        help=(
            "Target host CPU share for sync (1-100 or 'auto'). "
            "Derives file workers, local-embed concurrency, and Torch/OMP threads. "
            "Overrides AGENTCORE_SYNC_CPU_PERCENT for this run. "
            "Default: env AGENTCORE_SYNC_CPU_PERCENT or auto"
        ),
    )
    sync.add_argument(
        "--progress-interval",
        type=float,
        default=30.0,
        help="Seconds between progress lines (ETA adapts from observed file rate; default 30)",
    )
    sync.add_argument(
        "--allow-cloud-llm",
        action="store_true",
        help=(
            "Skip interactive cloud-LLM prompt: treat as explicit per-run consent "
            "to send code-derived prompts through a non-local LLM route"
        ),
    )
    sync.add_argument(
        "--skip-nonconforming",
        action="store_true",
        help=(
            "Skip syncing paths that fail Full-tier docs-standards "
            "(no interactive prompt; for scripts). "
            "Conflicts with --sync-nonconforming"
        ),
    )
    sync.add_argument(
        "--sync-nonconforming",
        action="store_true",
        help=(
            "Sync nonconforming docs/code anyway "
            "(skip the interactive standards gate). "
            "Conflicts with --skip-nonconforming"
        ),
    )
    sync.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Extra exclude (dir name or wildcard glob; repeatable). Requires agentcore.sync.yaml",
    )
    sync.add_argument(
        "--include-path",
        action="append",
        default=[],
        help="Only sync under this prefix/glob (repeatable). Requires agentcore.sync.yaml",
    )
    sync.add_argument(
        "--include-ext",
        action="append",
        default=[],
        help="Override include extensions (repeatable, e.g. --include-ext .py)",
    )

    llm = sub.add_parser("llm", help="LiteLLM gateway (test connectivity, sessions)")
    llm_sub = llm.add_subparsers(dest="llm_command", required=True)
    llm_sub.add_parser(
        "sessions",
        help="Show in-flight and recent RPM sessions (process-local snapshot)",
    )
    llm_test = llm_sub.add_parser(
        "test",
        help="Send a short prompt (default Hi) via configured LiteLLM model",
    )
    llm_test.add_argument(
        "--prompt",
        default="Hi",
        help="User prompt for the one-shot test (default: Hi)",
    )
    llm_test.add_argument(
        "--model",
        default=None,
        help="Override AGENTCORE_LITELLM_DEFAULT_MODEL for this call",
    )

    purge = sub.add_parser(
        "purge",
        help="Wipe project graph data only (requires --yes); then run sync to rebuild",
    )
    add_scope_args(purge, required=False)
    purge.add_argument(
        "--yes",
        action="store_true",
        help="Confirm destructive wipe of symbols/edges for this scope",
    )

    destroy = sub.add_parser(
        "destroy-profile",
        help=(
            "Delete this scope's AgentCore profile data (graph, identity, project state, "
            "env/connect pins, MCP entries). Does NOT delete source code. "
            "Requires two different typed confirmations in the terminal"
        ),
    )
    add_scope_args(destroy, required=False)

    list_profiles = sub.add_parser(
        "list-profiles",
        help="List local tenant/workspace/project profiles and show which scope is active",
    )
    list_profiles.add_argument("--json", action="store_true", help="Print JSON only")
    list_profiles.add_argument("--verbose", action="store_true", help="Human table + JSON")
