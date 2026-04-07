from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from api.services.sql_validator import validate_sql_allowed_tables


def run_sql_query(
    duckdb_path: str | Path,
    sql: str,
    *,
    allowed_table_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    # Enforce SQL safety and allowlisting before executing.
    if allowed_table_names is not None:
        validate_sql_allowed_tables(sql, allowed_table_names)

    con = duckdb.connect(str(duckdb_path), read_only=True)
    try:
        return con.execute(sql).fetchdf().to_dict("records")
    finally:
        con.close()
