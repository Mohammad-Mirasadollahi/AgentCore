"""Human and file text rendering for agentcore stats."""

from __future__ import annotations

from typing import Any

from agentcore_cli import ui


def format_bytes(n: int) -> str:
    value = float(max(0, int(n or 0)))
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024.0 or unit == "GB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{int(n)} B"


def format_language_line(row: dict[str, Any], *, detail: bool) -> str:
    lang = str(row.get("language") or "unknown")
    files = int(row.get("files") or 0)
    pct_code = row.get("percent_of_code")
    base = f"{lang}  files={files}  ({pct_code}% of code)  {format_bytes(int(row.get('bytes') or 0))}"
    if not detail:
        return (
            f"{base}  done={row.get('percent_done')}%  "
            f"edited={row.get('percent_edited')}%  remaining={row.get('percent_remaining')}%"
        )
    return (
        f"{base}  bytes={row.get('percent_of_bytes')}% of code bytes  "
        f"done {row.get('done_count')}/{files} ({row.get('percent_done')}%)  "
        f"edited {row.get('edited_count')}/{files} ({row.get('percent_edited')}%)  "
        f"remaining {row.get('remaining_count')}/{files} ({row.get('percent_remaining')}%)"
    )


def format_summary_lines(report: dict[str, Any]) -> list[str]:
    summary = report["summary"]
    totals = report.get("totals") or {}
    code = summary["code"]
    docs = summary["docs"]
    llm = summary["llm"]
    scope = report["scope"]
    return [
        "AgentCore stats",
        f"Scope: {scope['tenant']}/{scope['workspace']}/{scope['project']}",
        f"Paths: {len(report.get('paths') or [])}",
        (
            f"Totals: code_files={totals.get('code_files', 0)}  "
            f"code_bytes={format_bytes(int(totals.get('code_bytes') or 0))}  "
            f"docs_files={totals.get('docs_files', 0)}  "
            f"docs_bytes={format_bytes(int(totals.get('docs_bytes') or 0))}"
        ),
        (
            f"Code:  done {code['done_count']}/{code['total']} ({code['percent_done']}%)  "
            f"edited {code.get('edited_count', 0)}/{code['total']} ({code.get('percent_edited', 0)}%)  "
            f"remaining {code['remaining_count']}/{code['total']} ({code.get('percent_remaining', 0)}%)"
        ),
        (
            f"Docs:  done {docs['done_count']}/{docs['total']} ({docs['percent_done']}%)  "
            f"edited {docs.get('edited_count', 0)}/{docs['total']} ({docs.get('percent_edited', 0)}%)  "
            f"remaining {docs['remaining_count']}/{docs['total']} ({docs.get('percent_remaining', 0)}%)"
        ),
        f"LLM:   {llm['done_count']}/{llm['total']} symbols  ({llm['percent_done']}%)",
    ]


def format_detail_text(report: dict[str, Any]) -> str:
    chunks: list[str] = []
    chunks.extend(format_summary_lines(report))
    chunks.append("")
    chunks.append("By language:")
    languages = report.get("languages") or []
    if not languages:
        chunks.append("  (none)")
    else:
        for row in languages:
            chunks.append(f"  - {format_language_line(row, detail=True)}")
    chunks.append("")
    for root in report.get("results") or []:
        chunks.append(f"=== {root.get('path')} ===")
        totals = root.get("totals") or {}
        chunks.append(
            f"Totals: code={totals.get('code_files', 0)} files "
            f"({format_bytes(int(totals.get('code_bytes') or 0))})  "
            f"docs={totals.get('docs_files', 0)} files "
            f"({format_bytes(int(totals.get('docs_bytes') or 0))})"
        )
        for row in root.get("languages") or []:
            chunks.append(f"  - {format_language_line(row, detail=True)}")
        chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


def print_human(
    report: dict[str, Any],
    *,
    detail: bool,
    title: str = "Stats",
    show_hint: bool = True,
) -> None:
    summary = report["summary"]
    totals = report.get("totals") or {}
    ui.blank()
    ui.heading(title)
    ui.blank()
    scope = report["scope"]
    ui.kv("Scope", ui.scope_line(scope["tenant"], scope["workspace"], scope["project"]))
    for path in report.get("paths") or []:
        ui.bullet(str(path))

    ui.blank()
    ui.section("Totals")
    ui.kv(
        "Code",
        f"{totals.get('code_files', 0)} files  ({format_bytes(int(totals.get('code_bytes') or 0))})",
    )
    ui.kv(
        "Docs",
        f"{totals.get('docs_files', 0)} files  ({format_bytes(int(totals.get('docs_bytes') or 0))})",
    )

    ui.blank()
    ui.section("Processing")
    code = summary["code"]
    docs = summary["docs"]
    llm = summary["llm"]
    ui.kv("Code done", f"{code['done_count']}/{code['total']}  ({code['percent_done']}%)")
    ui.kv(
        "Code edited",
        f"{code.get('edited_count', 0)}/{code['total']}  ({code.get('percent_edited', 0)}%)  ← needs sync",
    )
    ui.kv(
        "Code remaining",
        f"{code['remaining_count']}/{code['total']}  ({code.get('percent_remaining', 0)}%)",
    )
    ui.kv("Docs done", f"{docs['done_count']}/{docs['total']}  ({docs['percent_done']}%)")
    ui.kv(
        "Docs edited",
        f"{docs.get('edited_count', 0)}/{docs['total']}  ({docs.get('percent_edited', 0)}%)  ← needs sync",
    )
    ui.kv(
        "Docs remaining",
        f"{docs['remaining_count']}/{docs['total']}  ({docs.get('percent_remaining', 0)}%)",
    )
    ui.kv("LLM", f"{llm['done_count']}/{llm['total']} symbols  ({llm['percent_done']}%)")

    ui.blank()
    ui.section("By language")
    languages = report.get("languages") or []
    if not languages:
        ui.bullet("(none)")
    else:
        for idx, row in enumerate(languages, start=1):
            ui.bullet(f"{idx}. {format_language_line(row, detail=detail)}")
    ui.blank()
    if show_hint:
        ui.bullet("Hint: agentcore stats detail | save <file> | detail save <file>")
        ui.blank()


def print_sync_preflight(report: dict[str, Any]) -> None:
    """Same snapshot as ``agentcore stats``, shown at the start of sync."""
    print_human(report, detail=False, title="Before sync", show_hint=False)
