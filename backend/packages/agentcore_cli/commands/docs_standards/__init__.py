"""Docs standards compliance CLI."""

from agentcore_cli.commands.docs_standards.cmd import cmd_docs_standards
from agentcore_cli.commands.docs_standards.collect import build_docs_standards_report
from agentcore_cli.commands.docs_standards.remediate import remediate_markdown_doc, remediate_tree
from agentcore_cli.commands.docs_standards.render import format_detail_text
from agentcore_cli.commands.docs_standards.scope import (
    DEFAULT_DOC_ROOTS,
    FULL_TIER_DOC_ROOTS,
    is_docs_audit_path,
    is_full_tier_doc_path,
)
from agentcore_cli.commands.docs_standards.words import parse_docs_standards_words

__all__ = [
    "DEFAULT_DOC_ROOTS",
    "FULL_TIER_DOC_ROOTS",
    "build_docs_standards_report",
    "cmd_docs_standards",
    "format_detail_text",
    "is_docs_audit_path",
    "is_full_tier_doc_path",
    "parse_docs_standards_words",
    "remediate_markdown_doc",
    "remediate_tree",
]
