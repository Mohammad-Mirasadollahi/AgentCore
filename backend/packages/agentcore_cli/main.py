"""AgentCore CLI entry point — parse args and dispatch to command modules."""

from __future__ import annotations

from agentcore_cli.util import ensure_service_import_paths, repo_root

ensure_service_import_paths()

from agentcore_cli.commands.connect import cmd_connect
from agentcore_cli.commands.client import (
    cmd_client_doctor_remote,
    cmd_client_list_mcp_clients,
    cmd_client_wire_remote,
)
from agentcore_cli.commands.cursor import cmd_cursor_export
from agentcore_cli.commands.doctor import cmd_doctor, cmd_version
from agentcore_cli.commands.init_cmd import cmd_init
from agentcore_cli.commands.paths_cmd import cmd_paths_add, cmd_paths_list, cmd_paths_remove
from agentcore_cli.commands.status import cmd_status
from agentcore_cli.commands.inventory import cmd_inventory
from agentcore_cli.commands.docs_standards import cmd_docs_standards
from agentcore_cli.commands.docs_suggest_links import cmd_docs_suggest_links
from agentcore_cli.commands.docs_catalog import cmd_docs_catalog
from agentcore_cli.commands.quality_audit import cmd_quality_audit
from agentcore_cli.commands.stats import cmd_stats
from agentcore_cli.commands.destroy_cmd import cmd_destroy_profile
from agentcore_cli.commands.list_profiles import cmd_list_profiles
from agentcore_cli.commands.sync import cmd_purge, cmd_sync
from agentcore_cli.commands.llm_cmd import cmd_llm_sessions, cmd_llm_test
from agentcore_cli.commands.graph import (
    cmd_graph_explore,
    cmd_graph_freshness,
    cmd_graph_generation_context,
    cmd_graph_hybrid,
    cmd_graph_ingest,
    cmd_graph_smoke,
    cmd_graph_watch,
)
from agentcore_cli.commands.mcp_cmd import (
    cmd_mcp_serve,
    cmd_mcp_serve_http,
    cmd_mcp_tokens,
    cmd_mcp_tools,
)
from agentcore_cli.commands.path_cmd import cmd_path_install
from agentcore_cli.commands.ports import cmd_ports_check, cmd_ports_show
from agentcore_cli.commands.approval import (
    cmd_approval_accept,
    cmd_approval_enqueue,
    cmd_approval_mode_set,
    cmd_approval_mode_show,
    cmd_approval_queue,
    cmd_approval_reject,
    cmd_approval_show,
)
from agentcore_cli.commands.profile import cmd_profile_list, cmd_profile_show
from agentcore_cli.commands.project import (
    cmd_project_activate,
    cmd_project_effective,
    cmd_project_register,
    cmd_project_show,
)
from agentcore_cli.commands.weight_profile import (
    cmd_weight_profile_activate,
    cmd_weight_profile_active,
    cmd_weight_profile_list,
    cmd_weight_profile_rollback,
    cmd_weight_profile_show,
    cmd_weight_profile_validate,
)
from agentcore_cli.commands.service_cmd import (
    cmd_boot_disable,
    cmd_boot_enable,
    cmd_service_detail,
    cmd_service_restart,
    cmd_service_start,
    cmd_service_status,
    cmd_service_stop,
)
from agentcore_cli.commands.upgrade import (
    cmd_upgrade_check,
    cmd_upgrade_client,
    cmd_upgrade_finalize,
    cmd_upgrade_plan,
    cmd_upgrade_prepare,
    cmd_upgrade_rollback,
    cmd_upgrade_run,
    cmd_upgrade_status,
    cmd_upgrade_versions,
)
from agentcore_cli.parser import build_parser

__all__ = ["build_parser", "main", "repo_root"]


def main(argv: list[str] | None = None) -> int:
    try:
        return _dispatch(argv)
    except KeyboardInterrupt:
        print("\nInterrupted — check: agentcore service status", flush=True)
        return 130


def _dispatch(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version and not args.command:
        return cmd_version(args)
    if not args.command:
        parser.print_help()
        return 2

    if args.command == "version":
        return cmd_version(args)
    if args.command == "doctor":
        return cmd_doctor(args)
    if args.command == "service":
        if args.service_command == "start":
            return cmd_service_start(args)
        if args.service_command == "stop":
            return cmd_service_stop(args)
        if args.service_command == "restart":
            return cmd_service_restart(args)
        if args.service_command == "status":
            return cmd_service_status(args)
        if args.service_command == "detail":
            return cmd_service_detail(args)
    if args.command == "boot":
        if args.boot_command == "enable":
            return cmd_boot_enable(args)
        if args.boot_command == "disable":
            return cmd_boot_disable(args)
    if args.command == "init":
        return cmd_init(args)
    if args.command == "status":
        return cmd_status(args)
    if args.command == "inventory":
        return cmd_inventory(args)
    if args.command == "docs-standards":
        return cmd_docs_standards(args)
    if args.command == "docs-suggest-links":
        return cmd_docs_suggest_links(args)
    if args.command == "docs-catalog":
        return cmd_docs_catalog(args)
    if args.command == "quality-audit":
        return cmd_quality_audit(args)
    if args.command == "stats":
        return cmd_stats(args)
    if args.command == "connect":
        return cmd_connect(args)
    if args.command == "sync":
        return cmd_sync(args)
    if args.command == "llm":
        if args.llm_command == "sessions":
            return cmd_llm_sessions(args)
        if args.llm_command == "test":
            return cmd_llm_test(args)
    if args.command == "purge":
        return cmd_purge(args)
    if args.command == "destroy-profile":
        return cmd_destroy_profile(args)
    if args.command == "list-profiles":
        return cmd_list_profiles(args)
    if args.command == "paths":
        if args.paths_command == "list":
            return cmd_paths_list(args)
        if args.paths_command == "add":
            return cmd_paths_add(args)
        if args.paths_command == "remove":
            return cmd_paths_remove(args)
    if args.command == "profile":
        if args.profile_command in (None, "list"):
            return cmd_profile_list(args)
        if args.profile_command == "show":
            return cmd_profile_show(args)
    if args.command == "project":
        if args.project_command == "register":
            return cmd_project_register(args)
        if args.project_command == "activate":
            return cmd_project_activate(args)
        if args.project_command == "show":
            return cmd_project_show(args)
        if args.project_command == "effective":
            return cmd_project_effective(args)
    if args.command == "cursor":
        if args.cursor_command == "export":
            return cmd_cursor_export(args)
    if args.command == "client":
        if args.client_command == "list-mcp-clients":
            return cmd_client_list_mcp_clients(args)
        if args.client_command == "wire-remote":
            return cmd_client_wire_remote(args)
        if args.client_command == "doctor-remote":
            return cmd_client_doctor_remote(args)
    if args.command == "mcp":
        if args.mcp_command == "tools":
            return cmd_mcp_tools(args)
        if args.mcp_command == "tokens":
            return cmd_mcp_tokens(args)
        if args.mcp_command == "serve":
            return cmd_mcp_serve(args)
        if args.mcp_command == "serve-http":
            return cmd_mcp_serve_http(args)
    if args.command == "path":
        if args.path_command == "install":
            return cmd_path_install(args)
    if args.command == "ports":
        if args.ports_command == "show":
            return cmd_ports_show(args)
        if args.ports_command == "check":
            return cmd_ports_check(args)
    if args.command == "graph":
        if args.graph_command == "ingest":
            return cmd_graph_ingest(args)
        if args.graph_command == "freshness":
            return cmd_graph_freshness(args)
        if args.graph_command == "explore":
            return cmd_graph_explore(args)
        if args.graph_command == "hybrid":
            return cmd_graph_hybrid(args)
        if args.graph_command == "generation-context":
            return cmd_graph_generation_context(args)
        if args.graph_command == "smoke":
            return cmd_graph_smoke(args)
        if args.graph_command == "watch":
            return cmd_graph_watch(args)
    if args.command == "approval":
        if args.approval_command == "mode":
            if args.approval_mode_command == "show":
                return cmd_approval_mode_show(args)
            if args.approval_mode_command == "set":
                return cmd_approval_mode_set(args)
        if args.approval_command == "queue":
            return cmd_approval_queue(args)
        if args.approval_command == "show":
            return cmd_approval_show(args)
        if args.approval_command == "enqueue":
            return cmd_approval_enqueue(args)
        if args.approval_command == "accept":
            return cmd_approval_accept(args)
        if args.approval_command == "reject":
            return cmd_approval_reject(args)
    if args.command == "weight-profile":
        if args.weight_profile_command == "list":
            return cmd_weight_profile_list(args)
        if args.weight_profile_command == "show":
            return cmd_weight_profile_show(args)
        if args.weight_profile_command == "validate":
            return cmd_weight_profile_validate(args)
        if args.weight_profile_command == "active":
            return cmd_weight_profile_active(args)
        if args.weight_profile_command == "activate":
            return cmd_weight_profile_activate(args)
        if args.weight_profile_command == "rollback":
            return cmd_weight_profile_rollback(args)
    if args.command == "upgrade":
        if args.upgrade_command == "versions":
            return cmd_upgrade_versions(args)
        if args.upgrade_command == "check":
            return cmd_upgrade_check(args)
        if args.upgrade_command == "plan":
            return cmd_upgrade_plan(args)
        if args.upgrade_command == "prepare":
            return cmd_upgrade_prepare(args)
        if args.upgrade_command == "run":
            return cmd_upgrade_run(args)
        if args.upgrade_command == "status":
            return cmd_upgrade_status(args)
        if args.upgrade_command == "rollback":
            return cmd_upgrade_rollback(args)
        if args.upgrade_command == "finalize":
            return cmd_upgrade_finalize(args)
        if args.upgrade_command == "client":
            return cmd_upgrade_client(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
