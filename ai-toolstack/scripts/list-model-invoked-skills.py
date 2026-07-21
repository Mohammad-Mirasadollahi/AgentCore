#!/usr/bin/env python3
"""List Cursor skills by model-invocation (context load every agent turn)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL_ROOTS = [
    REPO / "ai-toolstack" / "skills",
    REPO / "ai-toolstack" / "cursor-agent-config" / "global-skills",
]


def parse_frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    out: dict[str, str] = {}
    name = re.search(r"^name:\s*(.+)$", block, re.M)
    if name:
        out["name"] = name.group(1).strip()
    desc = re.search(
        r"^description:\s*(?:>\s*\n)?(.*?)(?=\n[a-zA-Z_#]|\n---|\Z)",
        block,
        re.M | re.S,
    )
    if desc:
        d = desc.group(1).strip()
        d = re.sub(r"\s+", " ", d)
        out["description"] = d
    if re.search(r"^disable-model-invocation:\s*true\s*$", block, re.M):
        out["disable_model"] = "true"
    return out


def main() -> int:
    rows: list[tuple[str, str, int, str, Path]] = []
    for root in SKILL_ROOTS:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("SKILL.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            fm = parse_frontmatter(text)
            rel = path.relative_to(REPO)
            desc = fm.get("description", "")
            desc_len = len(desc)
            mode = "user-only" if fm.get("disable_model") == "true" else "model-invoked"
            rows.append((mode, fm.get("name", path.parent.name), desc_len, desc[:120], rel))

    model = [r for r in rows if r[0] == "model-invoked"]
    user = [r for r in rows if r[0] == "user-only"]
    model.sort(key=lambda r: -r[2])

    print("# Model-invoked skills audit\n")
    roots_label = ", ".join(f"`{r.relative_to(REPO)}`" for r in SKILL_ROOTS if r.is_dir())
    print(f"Generated from {roots_label}.\n")
    print(
        "Skills **without** `disable-model-invocation: true` expose `description` "
        "to the agent every turn (context load). Trim: set `disable-model-invocation: true` "
        "for `/command`-only skills you invoke manually.\n"
    )
    print(f"| Count | Mode |")
    print(f"|-------|------|")
    print(f"| {len(model)} | model-invoked (costs context) |")
    print(f"| {len(user)} | user-only (no description in window) |")
    print("\n## Model-invoked (sorted by description length)\n")
    print("| Skill | ~desc chars | Path | Trim hint |")
    print("|-------|-------------|------|-----------|")
    for _, name, n, desc, rel in model:
        hint = "add `disable-model-invocation: true` if you only `/` invoke" if n > 80 else "short; keep if auto-match helps"
        print(f"| `{name}` | {n} | `{rel}` | {hint} |")
    print("\n## User-only (already trimmed)\n")
    for _, name, n, _desc, rel in user[:15]:
        print(f"- `{name}` — `{rel}`")
    if len(user) > 15:
        print(f"- … and {len(user) - 15} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
