"""Docs standards compliance CLI."""

from agentcore_cli.commands.docs_standards.cmd import cmd_docs_standards
from agentcore_cli.commands.docs_standards.collect import build_docs_standards_report
from agentcore_cli.commands.docs_standards.remediate import remediate_markdown_doc, remediate_tree
from agentcore_cli.commands.docs_standards.render import format_detail_text
from agentcore_cli.commands.docs_standards.words import parse_docs_standards_words

__all__ = [
    "build_docs_standards_report",
    "cmd_docs_standards",
    "format_detail_text",
    "parse_docs_standards_words",
    "remediate_markdown_doc",
    "remediate_tree",
]
