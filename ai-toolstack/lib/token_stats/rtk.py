"""Query RTK history.db for token savings in a time range."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def rtk_db_path() -> Path:
    return Path.home() / ".local/share/rtk/history.db"


def query_rtk(
    start: datetime,
    end: datetime,
    project_path: str | None = None,
) -> dict[str, Any]:
    db = rtk_db_path()
    if not db.is_file():
        return {
            "available": False,
            "calls": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "tokens_saved": 0,
            "savings_pct": 0.0,
        }

    start_s = start.isoformat()
    end_s = end.isoformat()
    sql = """
        SELECT COUNT(*),
               COALESCE(SUM(input_tokens), 0),
               COALESCE(SUM(output_tokens), 0),
               COALESCE(SUM(saved_tokens), 0)
        FROM commands
        WHERE timestamp >= ? AND timestamp <= ?
    """
    params: list[Any] = [start_s, end_s]
    if project_path:
        sql += " AND project_path = ?"
        params.append(project_path)

    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro&immutable=1", uri=True)
    try:
        row = con.execute(sql, params).fetchone()
    finally:
        con.close()

    calls, tin, tout, saved = row or (0, 0, 0, 0)
    pct = (100.0 * saved / tin) if tin else 0.0
    return {
        "available": True,
        "calls": int(calls),
        "tokens_in": int(tin),
        "tokens_out": int(tout),
        "tokens_saved": int(saved),
        "savings_pct": round(pct, 1),
    }


def query_rtk_top_commands(
    start: datetime,
    end: datetime,
    project_path: str | None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    db = rtk_db_path()
    if not db.is_file():
        return []
    sql = """
        SELECT original_cmd,
               COUNT(*) AS n,
               SUM(saved_tokens) AS saved,
               AVG(savings_pct) AS avg_pct
        FROM commands
        WHERE timestamp >= ? AND timestamp <= ?
    """
    params: list[Any] = [start.isoformat(), end.isoformat()]
    if project_path:
        sql += " AND project_path = ?"
        params.append(project_path)
    sql += " GROUP BY original_cmd ORDER BY saved DESC LIMIT ?"
    params.append(limit)

    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro&immutable=1", uri=True)
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    return [
        {
            "command": r[0],
            "count": int(r[1]),
            "tokens_saved": int(r[2] or 0),
            "avg_pct": round(float(r[3] or 0), 1),
        }
        for r in rows
    ]
