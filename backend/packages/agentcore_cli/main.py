"""AgentCore CLI entry point — parse args and dispatch to command modules."""

from __future__ import annotations

from agentcore_cli.commands.connect import cmd_connect
from agentcore_cli.commands.client import (
    cmd_client_doctor_remote,
    cmd_client_list_mcp_clients,
    cmd_client_wire_remote,
)
from agentcore_cli.commands.cursor import cmd_cursor_export
from agentcore_cli.commands.doctor import cmd_doctor, cmd_version
from agentcore_cli.commands.graph import (
    cmd_graph_explore,
    cmd_graph_freshness,
    cmd_graph_hybrid,
    cmd_graph_ingest,
    cmd_graph_smoke,
    cmd_graph_watch,
)
from agentcore_cli.commands.mcp_cmd import cmd_mcp_serve, cmd_mcp_serve_http, cmd_mcp_tools
from agentcore_cli.commands.path_cmd import cmd_path_install
from agentcore_cli.commands.ports import cmd_ports_check, cmd_ports_show
from agentcore_cli.commands.profile import cmd_profile_list, cmd_profile_show
from agentcore_cli.commands.project import (
    cmd_project_activate,
    cmd_project_effective,
    cmd_project_register,
    cmd_project_show,
)
from agentcore_cli.parser import build_parser
from agentcore_cli.util import repo_root

__all__ = ["build_parser", "main", "repo_root"]


def main(argv: list[str] | None = None) -> int:
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
    if args.command == "connect":
        return cmd_connect(args)
    if args.command == "profile":
        if args.profile_command == "list":
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
        if args.graph_command == "smoke":
            return cmd_graph_smoke(args)
        if args.graph_command == "watch":
            return cmd_graph_watch(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
