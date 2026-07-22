"""Argument parser for the agentcore CLI."""

from __future__ import annotations

import argparse
import sys

from agentcore_cli.util import add_scope_args

_SYNC_MAX_FILE_DASHED = frozenset({"-max-file", "--max-file", "-max-files", "--max-files"})
_DEFAULT_SYNC_MAX_FILES = 2000


def _peel_sync_max_file(argv: list[str], error) -> tuple[list[str], int | None]:
    """Accept bare ``max-file N`` on sync; reject dashed spellings."""
    if not argv or argv[0] != "sync":
        return argv, None
    out: list[str] = []
    override: int | None = None
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in _SYNC_MAX_FILE_DASHED:
            error("use max-file <n> (no leading dashes)")
        if tok == "max-file":
            if i + 1 >= len(argv):
                error("argument max-file: expected one integer argument")
            try:
                override = int(argv[i + 1])
            except ValueError:
                error(f"argument max-file: invalid int value: {argv[i + 1]!r}")
            i += 2
            continue
        out.append(tok)
        i += 1
    return out, override


class _AgentCoreArgumentParser(argparse.ArgumentParser):
    def parse_known_args(self, args=None, namespace=None):
        if args is None:
            args = sys.argv[1:]
        args, max_files_override = _peel_sync_max_file(list(args), self.error)
        ns, rest = super().parse_known_args(args, namespace)
        if max_files_override is not None:
            ns.max_files = max_files_override
        return ns, rest


def build_parser() -> argparse.ArgumentParser:
    parser = _AgentCoreArgumentParser(
        prog="agentcore",
        description="AgentCore CLI — manage Usage Profiles, projects, and Cursor MCP",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Show CLI version and repo root")
    sub.add_parser("doctor", help="Check venv, imports, profiles, and PATH")

    service = sub.add_parser(
        "service",
        help="Start/stop/restart/status for Compose infra + MCP HTTP backend",
    )
    service_sub = service.add_subparsers(dest="service_command", required=True)
    service_sub.add_parser("start", help="Start postgres/neo4j + MCP HTTP daemon")
    service_sub.add_parser("stop", help="Stop MCP HTTP daemon + postgres/neo4j")
    service_sub.add_parser("restart", help="Restart Compose infra + MCP HTTP")
    service_status = service_sub.add_parser(
        "status",
        help="Show Compose + MCP HTTP + boot enablement",
    )
    service_status.add_argument("--json", action="store_true", help="Print JSON only")
    service_detail = service_sub.add_parser(
        "detail",
        help="Status plus MCP HTTP / unhealthy Compose log tails (for failed starts)",
    )
    service_detail.add_argument("--json", action="store_true", help="Print JSON only")

    boot = sub.add_parser("boot", help="Enable/disable AgentCore start on system boot")
    boot_sub = boot.add_subparsers(dest="boot_command", required=True)
    boot_enable = boot_sub.add_parser("enable", help="Install and enable systemd unit")
    boot_enable.add_argument(
        "--user",
        action="store_true",
        help="Use systemd --user unit (~/.config/systemd/user)",
    )
    boot_disable = boot_sub.add_parser("disable", help="Disable and remove systemd unit")
    boot_disable.add_argument(
        "--user",
        action="store_true",
        help="Target systemd --user unit",
    )

    init = sub.add_parser(
        "init",
        help="Create tenant + workspace, pin software path(s), then save them",
    )
    init.add_argument("--name", default="", help="Display name (default: OS username)")
    init.add_argument("--tenant", required=True, help="Tenant id you choose (e.g. acme)")
    init.add_argument("--workspace", required=True, help="First workspace id you choose (e.g. eng)")
    init.add_argument(
        "--project",
        default="",
        help="Project id you choose (default: current directory name)",
    )
    init.add_argument("--project-name", default="", help="Human project title")
    init.add_argument(
        "--path",
        action="append",
        default=[],
        help="Software root directory to sync (required on create; repeatable for multiple apps)",
    )
    init.add_argument(
        "--usage-profile",
        default="programming-cursor-mcp",
        help="Usage profile for the first project",
    )
    init.add_argument("--force", action="store_true", help="Replace existing ~/.agentcore/identity.yaml")

    status = sub.add_parser(
        "status",
        help="Show platform + graph sync status (one command)",
    )
    add_scope_args(status, required=False)
    status.add_argument("--json", action="store_true", help="Print full JSON only")
    status.add_argument("--verbose", action="store_true", help="Human summary + JSON")

    inventory = sub.add_parser(
        "inventory",
        help="List code/docs done vs remaining for pinned client software roots",
        epilog="Modes (no dashed flags): agentcore inventory | agentcore inventory detail | "
        "agentcore inventory save <file> | agentcore inventory detail save <file>",
    )
    inventory.add_argument(
        "words",
        nargs="*",
        help="Optional words: detail | save <path> | detail save <path>",
    )

    docs_standards = sub.add_parser(
        "docs-standards",
        help="Report which docs/ Markdown files fail AgentCore documentation standards",
        epilog="Modes (no dashed flags): agentcore docs-standards | agentcore docs-standards detail | "
        "agentcore docs-standards save <file> | agentcore docs-standards detail save <file>",
    )
    docs_standards.add_argument(
        "words",
        nargs="*",
        help="Optional words: detail | save <path> | detail save <path>",
    )

    stats = sub.add_parser(
        "stats",
        help="Count code/docs, language mix, and processed vs remaining percents",
        epilog="Modes (no dashed flags): agentcore stats | agentcore stats detail | "
        "agentcore stats save <file> | agentcore stats detail save <file>",
    )
    stats.add_argument(
        "words",
        nargs="*",
        help="Optional words: detail | save <path> | detail save <path>",
    )

    connect = sub.add_parser("connect", help="One-command coding-agent onboarding (see connect.yaml)")
    connect.add_argument("--init", action="store_true", help="Write ~/.agentcore/connect.yaml template")
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
    sync.set_defaults(max_files=_DEFAULT_SYNC_MAX_FILES)
    sync.epilog = "Limit file count with bare: max-file <n>  (example: agentcore sync max-file 50)"
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

    llm = sub.add_parser("llm", help="LiteLLM gateway observability")
    llm_sub = llm.add_subparsers(dest="llm_command", required=True)
    llm_sub.add_parser(
        "sessions",
        help="Show in-flight and recent RPM sessions (process-local snapshot)",
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

    paths = sub.add_parser(
        "paths",
        help="List / add / remove pinned software roots used by sync",
    )
    paths_sub = paths.add_subparsers(dest="paths_command", required=True)
    paths_sub.add_parser("list", help="Show pinned software paths")
    paths_add = paths_sub.add_parser("add", help="Add one or more software roots")
    paths_add.add_argument(
        "path",
        nargs="+",
        help="Directory path(s) to add",
    )
    paths_rm = paths_sub.add_parser(
        "remove",
        help="Remove software root(s); graph data for removed trees is kept until purge",
    )
    paths_rm.add_argument(
        "path",
        nargs="+",
        help="Directory path(s) to remove from the pin list",
    )

    profile = sub.add_parser("profile", help="Usage Profile catalog commands")
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)
    profile_sub.add_parser("list", help="List Usage Profiles")
    show = profile_sub.add_parser("show", help="Show one Usage Profile JSON")
    show.add_argument("profile_id")

    project = sub.add_parser("project", help="Local project + Usage Profile state")
    project_sub = project.add_subparsers(dest="project_command", required=True)

    reg = project_sub.add_parser("register", help="Register a local project state file")
    add_scope_args(reg)
    reg.add_argument("--name", default="")
    reg.add_argument("--usage-profile", default="default")
    reg.add_argument("--domain-pack", default="")
    reg.add_argument("--feature-profile", default="")
    reg.add_argument("--force", action="store_true")

    act = project_sub.add_parser("activate", help="Activate a Usage Profile on a project")
    add_scope_args(act)
    act.add_argument("--usage-profile", required=True)
    act.add_argument("--apply-catalog-defaults", action=argparse.BooleanOptionalAction, default=True)

    show_p = project_sub.add_parser("show", help="Show local project state")
    add_scope_args(show_p)
    eff = project_sub.add_parser("effective", help="Resolve effective Usage Profile")
    add_scope_args(eff)

    cursor = sub.add_parser("cursor", help="Cursor MCP helpers")
    cursor_sub = cursor.add_subparsers(dest="cursor_command", required=True)
    export = cursor_sub.add_parser("export", help="Export mcpServers fragment for Cursor")
    add_scope_args(export)
    export.add_argument("--out", default="", help="Write JSON to this path")

    mcp = sub.add_parser("mcp", help="MCP gateway helpers")
    mcp_sub = mcp.add_subparsers(dest="mcp_command", required=True)
    tools = mcp_sub.add_parser("tools", help="List MCP tools for a Usage Profile")
    tools.add_argument("--usage-profile", default="programming-cursor-mcp")
    serve = mcp_sub.add_parser("serve", help="Run MCP gateway on stdio for a project scope")
    add_scope_args(serve)
    serve.add_argument("--usage-profile", default="")
    serve_http = mcp_sub.add_parser(
        "serve-http",
        help="Run Streamable HTTP MCP gateway (Phase B; concurrent agents)",
    )
    serve_http.add_argument("--host", default="")
    serve_http.add_argument("--port", type=int, default=0)
    serve_http.add_argument("--usage-profile", default="programming-cursor-mcp")

    client = sub.add_parser("client", help="Dev host wiring to a remote AgentCore install")
    client_sub = client.add_subparsers(dest="client_command", required=True)
    client_sub.add_parser("list-mcp-clients", help="List supported coding-agent MCP config targets")
    wire = client_sub.add_parser("wire-remote", help="Write MCP configs (SSH stdio to AgentCore host)")
    add_scope_args(wire)
    wire.add_argument("--ssh", required=True, help="SSH target user@host for AgentCore server")
    wire.add_argument("--remote-root", required=True, help="AgentCore root on server (e.g. /opt/AgentCore)")
    wire.add_argument("--out", default="", help="Merge into this mcp.json path")
    wire.add_argument(
        "--project-dir",
        default="",
        help="Application repo root (default: cwd); used when --out is omitted",
    )
    wire.add_argument("--server-name", default="", help="MCP server key (default: AgentCore-Programming)")
    wire.add_argument("--register", action="store_true", help="Register/activate project on server")
    wire.add_argument("--project-name", default="", help="Project display name for --register")
    wire.add_argument("--usage-profile", default="programming-cursor-mcp")
    wire.add_argument("--remote-python", default="", help="Override remote venv python path")
    wire.add_argument(
        "--remote-os",
        choices=("unix", "windows"),
        default="unix",
        help="AgentCore host OS (venv layout)",
    )
    wire.add_argument(
        "--clients",
        default="all",
        help="Comma-separated client ids or 'all' (default: all project-scoped targets)",
    )
    wire.add_argument(
        "--include-user-clients",
        action="store_true",
        help="Also merge into user-global configs (cursor-user, claude-desktop)",
    )
    wire.add_argument("--skip-doctor", action="store_true", help="Skip remote python presence check")
    wire.add_argument("--dry-run", action="store_true", help="Print fragment only")
    doc = client_sub.add_parser("doctor-remote", help="Check SSH access to remote MCP serve entrypoint")
    doc.add_argument("--ssh", required=True)
    doc.add_argument("--remote-root", required=True)
    doc.add_argument("--remote-python", default="")
    doc.add_argument("--remote-os", choices=("unix", "windows"), default="unix")

    path_cmd = sub.add_parser("path", help="Install agentcore onto user PATH")
    path_sub = path_cmd.add_subparsers(dest="path_command", required=True)
    install = path_sub.add_parser("install", help="Symlink ~/.local/bin/agentcore -> .venv/bin/agentcore")
    install.add_argument(
        "--shell-rc",
        default="",
        help="Optional rc file to append PATH export (e.g. .bashrc)",
    )

    ports = sub.add_parser("ports", help="Port profile preflight")
    ports_sub = ports.add_subparsers(dest="ports_command", required=True)
    ports_show = ports_sub.add_parser("show", help="Show resolved ports from profile (env overrides)")
    ports_show.add_argument("--profile", default="", help="Port profile JSON path (default: agentcore-dev)")
    ports_check = ports_sub.add_parser("check", help="Check that profile ports are free to bind")
    ports_check.add_argument("--profile", default="", help="Port profile JSON path (default: agentcore-dev)")

    graph = sub.add_parser("graph", help="Code-graph operator smoke (ingest / freshness / explore / hybrid)")
    graph_sub = graph.add_subparsers(dest="graph_command", required=True)

    gin = graph_sub.add_parser("ingest", help="Ingest a repository root into the code graph")
    add_scope_args(gin)
    gin.add_argument("--path", required=True, help="Repository or source root to ingest")
    gin.add_argument("--max-files", type=int, default=200)
    gin.add_argument("--allow-cloud-llm", action="store_true")

    gfr = graph_sub.add_parser("freshness", help="Show freshness / pending-sync status")
    add_scope_args(gfr)
    gfr.add_argument("--mark-pending", default="", help="Optional file path to mark pending")

    gex = graph_sub.add_parser("explore", help="Run explore pack for a query")
    add_scope_args(gex)
    gex.add_argument("--query", required=True)
    gex.add_argument("--top-k", type=int, default=12)
    gex.add_argument("--allow-cloud-llm", action="store_true")

    ghy = graph_sub.add_parser("hybrid", help="Run hybrid search")
    add_scope_args(ghy)
    ghy.add_argument("--query", required=True)
    ghy.add_argument("--top-k", type=int, default=10)
    ghy.add_argument("--allow-cloud-llm", action="store_true")

    gsm = graph_sub.add_parser("smoke", help="Ingest + freshness + hybrid + explore in one process")
    add_scope_args(gsm)
    gsm.add_argument("--path", required=True)
    gsm.add_argument("--query", default="login password")
    gsm.add_argument("--max-files", type=int, default=50)
    gsm.add_argument("--allow-cloud-llm", action="store_true")

    gwa = graph_sub.add_parser(
        "watch",
        help="Batched poll sidecar for pending-sync (debounce; not per-edit / not continuous index)",
    )
    add_scope_args(gwa)
    gwa.add_argument("--path", required=True)
    gwa.add_argument("--interval", type=float, default=2.0, help="Poll interval seconds")
    gwa.add_argument(
        "--debounce",
        type=float,
        default=30.0,
        help="Quiet seconds before flushing a change batch (agent-coding safe)",
    )
    gwa.add_argument(
        "--max-wait",
        type=float,
        default=120.0,
        help="Max seconds to hold a batch while files keep changing",
    )
    gwa.add_argument("--once", action="store_true", help="Single poll cycle then exit")

    return parser
