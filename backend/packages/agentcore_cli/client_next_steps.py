"""Post-install / post-upgrade next steps for coding-agent (client) hosts.

Usage Profile id is never set during client install — only at ``agentcore connect``.
"""

from __future__ import annotations

from agentcore_cli import ui

# English operator copy (install banners + upgrade client). Keep in sync with docs/41.
CLIENT_USAGE_PROFILE_NEXT_STEPS = """\
Usage Profile id (set at connect — not during client install/upgrade):

  List ids:
    agentcore profile list

  Interactive (from your app repo):
    cd /path/to/YourApp
    agentcore connect
    # Wizard asks for Usage Profile: enter an id or list number

  Non-interactive — remote AgentCore server (SSH):
    agentcore connect --usage-profile programming-cursor-mcp \\
      --tenant TENANT --workspace WORKSPACE \\
      --ssh user@agentcore-host

  Non-interactive — same-host dogfood (local stdio):
    agentcore connect --local --usage-profile programming-cursor-mcp \\
      --tenant TENANT --workspace WORKSPACE

  Non-interactive — connect.yaml already has usage_profile: <id>:
    agentcore connect --config .agentcore/connect.yaml

  Multi-app:
    agentcore connect /opt/App1,/opt/App2 --usage-profile programming-cursor-mcp \\
      --tenant TENANT --workspace WORKSPACE --ssh user@agentcore-host
"""


def print_client_connect_next_steps(*, heading: str = "Next — Usage Profile id") -> None:
    """Print how to set Usage Profile via interactive and non-interactive connect."""
    ui.blank()
    ui.heading(heading)
    ui.blank()
    for line in CLIENT_USAGE_PROFILE_NEXT_STEPS.strip().splitlines():
        print(f"   {line}" if line else "", flush=True)
    ui.blank()
    ui.next_steps(
        [
            "Docs: docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md",
        ]
    )
    ui.blank()
