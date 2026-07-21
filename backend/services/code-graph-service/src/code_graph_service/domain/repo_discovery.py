"""Discover supported source files under a repository root for bulk ingest."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .errors import ValidationError
from .languages import EXTENSION_TO_LANGUAGE, detect_language_from_path

# Operator excludes live in agentcore.sync.yaml (not hardcoded here).
# Empty defaults keep discovery APIs stable when callers pass explicit lists.
DEFAULT_EXCLUDE_DIRS: frozenset[str] = frozenset()
DEFAULT_EXCLUDE_GLOBS: tuple[str, ...] = ()

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


def _looks_like_glob(pattern: str) -> bool:
    return any(ch in pattern for ch in "*?[")


def _normalize_glob(pattern: str) -> str:
    return pattern.strip().replace("\\", "/").lstrip("./")


def path_matches_glob(relative_path: str, pattern: str) -> bool:
    """Match ``relative_path`` against a user/builtin glob (``*``, ``?``, ``[]``, ``**``).

    Leading ``**/`` matches zero or more directories (so ``**/src/**`` matches ``src/a.py``).
    """
    rel = relative_path.replace("\\", "/").lstrip("./")
    pat = _normalize_glob(pattern)
    if not pat:
        return False

    candidates = [pat]
    # ``**/foo`` ≡ ``foo`` at repo root (zero directories before foo).
    if pat.startswith("**/"):
        candidates.append(pat[3:])
    # ``foo/**`` also matches the directory path ``foo`` itself.
    if pat.endswith("/**"):
        candidates.append(pat[:-3].rstrip("/"))

    for candidate in candidates:
        if not candidate:
            continue
        if fnmatch.fnmatch(rel, candidate):
            return True
        if fnmatch.fnmatch(Path(rel).name, candidate):
            return True
    # Treat bare ``docs``-style patterns as directory-name matches via glob too.
    if not _looks_like_glob(pat) and "/" not in pat:
        return any(part.lower() == pat.lower() for part in Path(rel).parts[:-1])
    return False


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


def _matches_any_glob(relative_path: str, patterns: Iterable[str]) -> bool:
    return any(path_matches_glob(relative_path, p) for p in patterns if str(p).strip())


def _matches_include(relative: Path, patterns: list[str]) -> bool:
    if not patterns:
        return True
    rel = str(relative).replace("\\", "/")
    for raw in patterns:
        pat = raw.strip().replace("\\", "/").strip("/")
        if not pat:
            continue
        if _looks_like_glob(pat) or pat.endswith("/**"):
            if path_matches_glob(rel, pat if _looks_like_glob(pat) or "**" in pat else f"{pat}/**"):
                return True
            if path_matches_glob(rel, pat):
                return True
            continue
        # Plain prefix
        if rel == pat or rel.startswith(pat + "/"):
            return True
    return False


def discover_source_files(
    root_path: str | Path,
    *,
    include_extensions: Iterable[str] | None = None,
    exclude_dirs: Iterable[str] | None = None,
    exclude_globs: Iterable[str] | None = None,
    include_path_prefixes: Iterable[str] | None = None,
    max_files: int = DEFAULT_MAX_FILES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> list[DiscoveredFile]:
    """Walk ``root_path`` and return supported source files (sorted by relative path).

    Skips excluded directory names, exclude globs, hidden parents, oversized files,
    and undetectable languages. Optional include patterns/prefixes narrow the tree.
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
        if str(name).strip() and not _looks_like_glob(str(name))
    }
    globs = [
        _normalize_glob(str(p))
        for p in (
            exclude_globs
            if exclude_globs is not None
            else DEFAULT_EXCLUDE_GLOBS
        )
        if str(p).strip()
    ]
    # Plain exclude_dirs entries that look like globs join the glob list.
    if exclude_dirs is not None:
        for name in exclude_dirs:
            text = str(name).strip()
            if text and _looks_like_glob(text):
                globs.append(_normalize_glob(text))
    include_patterns = [
        str(p).strip().replace("\\", "/")
        for p in (include_path_prefixes or [])
        if str(p).strip()
    ]

    discovered: list[DiscoveredFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        rel_s = str(relative).replace("\\", "/")
        if _should_skip_parents(relative, excluded):
            continue
        if _matches_any_glob(rel_s, globs):
            continue
        if not _matches_include(relative, include_patterns):
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
                relative_path=rel_s,
                language=language,
                size_bytes=size,
            )
        )
        if len(discovered) >= max_files:
            break

    return discovered
