"""Discover supported source files under a repository root for bulk ingest."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .errors import ValidationError
from .languages import EXTENSION_TO_LANGUAGE, detect_language_from_path

DEFAULT_EXCLUDE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
        "target",
        "vendor",
        ".idea",
        ".vscode",
        "coverage",
        ".turbo",
        ".next",
        "Pods",
        ".eggs",
    }
)

DEFAULT_MAX_FILES = 2000
DEFAULT_MAX_FILE_BYTES = 1_500_000  # ~1.5 MiB


@dataclass(frozen=True)
class DiscoveredFile:
    """One source file eligible for code-graph ingest."""

    absolute_path: str
    relative_path: str
    language: str
    size_bytes: int


def default_include_extensions() -> tuple[str, ...]:
    return tuple(sorted(EXTENSION_TO_LANGUAGE.keys(), key=len, reverse=True))


def _normalize_extensions(include_extensions: Iterable[str] | None) -> set[str]:
    raw = include_extensions if include_extensions is not None else default_include_extensions()
    return {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in raw}


def _should_skip_parents(relative: Path, excluded: set[str]) -> bool:
    for part in relative.parts[:-1]:
        lower = part.lower()
        if lower in excluded:
            return True
        if lower.startswith("."):
            return True
        if lower.endswith(".egg-info"):
            return True
    return False


def discover_source_files(
    root_path: str | Path,
    *,
    include_extensions: Iterable[str] | None = None,
    exclude_dirs: Iterable[str] | None = None,
    max_files: int = DEFAULT_MAX_FILES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> list[DiscoveredFile]:
    """Walk ``root_path`` and return supported source files (sorted by relative path).

    Skips excluded directory names, hidden parent directories, oversized files,
    and paths whose language cannot be detected from the extension matrix.
    """
    root = Path(root_path).expanduser().resolve()
    if not root.exists():
        raise ValidationError(f"root_path does not exist: {root}")
    if not root.is_dir():
        raise ValidationError(f"root_path is not a directory: {root}")

    max_files = max(1, min(int(max_files), 20_000))
    max_file_bytes = max(1, int(max_file_bytes))
    extensions = _normalize_extensions(include_extensions)
    excluded = {
        str(name).strip().lower()
        for name in (exclude_dirs if exclude_dirs is not None else DEFAULT_EXCLUDE_DIRS)
        if str(name).strip()
    }

    discovered: list[DiscoveredFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if _should_skip_parents(relative, excluded):
            continue

        language = detect_language_from_path(str(relative))
        if language is None:
            continue
        name_lower = path.name.lower()
        if not any(name_lower.endswith(ext) for ext in extensions):
            continue

        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size <= 0 or size > max_file_bytes:
            continue

        discovered.append(
            DiscoveredFile(
                absolute_path=str(path),
                relative_path=str(relative).replace("\\", "/"),
                language=language,
                size_bytes=size,
            )
        )
        if len(discovered) >= max_files:
            break

    return discovered
