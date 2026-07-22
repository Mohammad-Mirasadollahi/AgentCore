"""Inventory collection facade — public imports stay stable here."""

from __future__ import annotations

from agentcore_cli.commands.inventory.languages import language_breakdown
from agentcore_cli.commands.inventory.report import build_inventory_report
from agentcore_cli.commands.inventory.root import inventory_one_root

__all__ = [
    "build_inventory_report",
    "inventory_one_root",
    "language_breakdown",
]
