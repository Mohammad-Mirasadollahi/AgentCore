"""Resolve local language-server launch commands (no cloud)."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageServerSpec:
    language: str
    argv: list[str]


_ENV_KEYS = {
    "python": "AGENTCORE_LSP_CMD_PYTHON",
    "typescript": "AGENTCORE_LSP_CMD_TYPESCRIPT",
    "javascript": "AGENTCORE_LSP_CMD_JAVASCRIPT",
    "go": "AGENTCORE_LSP_CMD_GO",
    "rust": "AGENTCORE_LSP_CMD_RUST",
}

_DEFAULT_CANDIDATES: dict[str, list[list[str]]] = {
    "python": [
        ["basedpyright-langserver", "--stdio"],
        ["pyright-langserver", "--stdio"],
    ],
    "typescript": [["typescript-language-server", "--stdio"]],
    "javascript": [["typescript-language-server", "--stdio"]],
    "go": [["gopls", "serve"]],
    "rust": [["rust-analyzer"]],
}


def normalize_edit_language(language: str, file_path: str = "") -> str:
    lang = (language or "").strip().lower()
    if lang in _ENV_KEYS:
        return lang
    lower = file_path.replace("\\", "/").lower()
    if lower.endswith((".ts", ".tsx", ".mts", ".cts")):
        return "typescript"
    if lower.endswith((".js", ".jsx", ".mjs", ".cjs")):
        return "javascript"
    if lower.endswith(".go"):
        return "go"
    if lower.endswith(".rs"):
        return "rust"
    if lower.endswith(".py"):
        return "python"
    return lang or "python"


def resolve_language_server(language: str, file_path: str = "") -> LanguageServerSpec | None:
    """Return argv for a local LS, or None if not installed / not configured."""
    lang = normalize_edit_language(language, file_path)
    env_key = _ENV_KEYS.get(lang)
    if env_key:
        raw = (os.environ.get(env_key) or "").strip()
        if raw:
            parts = raw.split()
            if parts:
                return LanguageServerSpec(language=lang, argv=parts)
    for candidate in _DEFAULT_CANDIDATES.get(lang, []):
        if candidate and shutil.which(candidate[0]):
            return LanguageServerSpec(language=lang, argv=list(candidate))
    return None


def lsp_edit_session_enabled() -> bool:
    """Feature gate: default on; set AGENTCORE_LSP_EDIT_SESSION=0 to disable."""
    raw = (os.environ.get("AGENTCORE_LSP_EDIT_SESSION") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}
