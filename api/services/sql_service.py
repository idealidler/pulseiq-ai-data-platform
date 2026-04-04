from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb


def run_sql_query(duckdb_path: str | Path, sql: str) -> list[dict[str, Any]]:
    normalized = sql.lower()
    stripped = normalized.strip()
    if not (stripped.startswith("select") or stripped.startswith("with")):
        raise ValueError("Only SELECT queries are allowed.")
    if any(keyword in normalized for keyword in ["insert ", "update ", "delete ", "drop ", "alter "]):
        raise ValueError("Mutating SQL is not allowed.")

    con = duckdb.connect(str(duckdb_path), read_only=True)
    try:
        return con.execute(sql).fetchdf().to_dict("records")
    finally:
        con.close()
