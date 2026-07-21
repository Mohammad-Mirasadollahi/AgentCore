"""Package-manager manifest aliases for IMPORT resolution (GAP-002 / Phase F3).

Reads lightweight maps from pyproject.toml, go.mod, and package.json so imports
like ``@app/utils`` or ``example.com/mod/pkg`` resolve to project file stems.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def load_package_aliases(root: str | Path) -> dict[str, str]:
    """Return import-prefix → path-stem (or module path) aliases for a repo root."""
    root_path = Path(root)
    aliases: dict[str, str] = {}
    if not root_path.is_dir():
        return aliases
    aliases.update(_from_pyproject(root_path / "pyproject.toml"))
    aliases.update(_from_go_mod(root_path / "go.mod"))
    aliases.update(_from_package_json(root_path / "package.json"))
    return aliases


def rewrite_import(import_text: str, aliases: dict[str, str]) -> str:
    """Rewrite an import using the longest matching alias prefix."""
    raw = (import_text or "").strip().strip("\"'")
    if not raw or not aliases:
        return raw
    best = ""
    replacement = ""
    for prefix, target in aliases.items():
        if raw == prefix or raw.startswith(prefix + "/") or raw.startswith(prefix + "."):
            if len(prefix) > len(best):
                best = prefix
                replacement = target
    if not best:
        return raw
    rest = raw[len(best) :].lstrip("/.")
    if not rest:
        return replacement
    return f"{replacement}/{rest}".replace("\\", "/")


def _from_pyproject(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    # Minimal TOML scrape — avoid new dependency.
    name = _toml_string(text, "name")
    if not name:
        return {}
    # Map distribution name to importable package guess (hyphens → underscores).
    pkg = name.replace("-", "_")
    return {name: pkg, pkg: pkg}


def _from_go_mod(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("module "):
            module = line.split(None, 1)[1].strip()
            if module:
                return {module: module}
    return {}


def _from_package_json(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    out: dict[str, str] = {}
    name = str(data.get("name") or "").strip()
    if name:
        out[name] = name.lstrip("@").replace("/", ".")
    imports = data.get("imports")
    if isinstance(imports, dict):
        for key, value in imports.items():
            if not isinstance(key, str):
                continue
            target = value if isinstance(value, str) else (value or {}).get("default") if isinstance(value, dict) else None
            if isinstance(target, str) and target:
                clean_key = key.rstrip("*").rstrip("/")
                clean_target = target.replace("*", "").rstrip("/")
                # "#utils/*" → stem under src if present
                stem = Path(clean_target).stem or clean_target
                out[clean_key] = stem
    return out


def _toml_string(text: str, key: str) -> str | None:
    pattern = re.compile(rf'^{re.escape(key)}\s*=\s*"([^"]+)"', re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else None
