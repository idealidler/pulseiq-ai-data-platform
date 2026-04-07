from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable


_MUTATION_KEYWORDS_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|merge)\b",
    flags=re.IGNORECASE,
)


def _normalize_identifier(name: str) -> str:
    # DuckDB identifiers are case-insensitive by default.
    return name.strip().strip('"').lower()


def _validate_single_statement(sql: str) -> None:
    # Most LLM SQL generators add a trailing semicolon. Allow exactly one terminal semicolon.
    s = sql.strip()
    if not s:
        raise ValueError("SQL is empty.")

    # If there is a semicolon not at the very end, we treat it as multi-statement SQL.
    trimmed = s[:-1].rstrip() if s.endswith(";") else s
    if ";" in trimmed:
        raise ValueError("Only a single SQL statement is allowed.")


def _validate_readonly_select(sql: str) -> None:
    normalized = sql.strip().lower()
    if not (normalized.startswith("select") or normalized.startswith("with")):
        raise ValueError("Only SELECT queries (with optional CTEs) are allowed.")
    if _MUTATION_KEYWORDS_RE.search(sql):
        raise ValueError("Mutating SQL is not allowed.")


def _allowed_table_set(allowed_table_names: Iterable[str]) -> set[str]:
    return {_normalize_identifier(t) for t in allowed_table_names}


def _extract_tables_regex(sql: str) -> set[str]:
    """
    Conservative fallback when sqlglot isn't installed.

    This is intentionally strict (only FROM/JOIN identifiers) to avoid false positives,
    but it can still miss edge-case SQL.
    """
    # Attempt to ignore CTE aliases in WITH clauses.
    cte_names: set[str] = set()
    # Examples:
    #   WITH cte AS (SELECT ...) SELECT ...
    #   WITH cte1 AS (...), cte2 AS (...) SELECT ...
    for m in re.finditer(r"(?:\bwith\b|,)\s*([a-zA-Z_][\w]*)\s+as\s*\(", sql, flags=re.IGNORECASE):
        cte_names.add(_normalize_identifier(m.group(1)))

    tables: set[str] = set()
    # FROM <table> ... or JOIN <table> ...
    pattern = re.compile(
        r"\b(?:from|join)\s+([a-zA-Z_][\w\.]*)",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(sql):
        raw = match.group(1)
        # strip schema prefix if present
        name = _normalize_identifier(raw.split(".")[-1])
        if name in cte_names:
            continue
        tables.add(name)
    return tables


@lru_cache(maxsize=512)
def _extract_tables_sqlglot(sql: str) -> frozenset[str]:
    """
    Extract referenced table names from SQL AST.
    Cached for performance because we may validate repeated SQL strings.
    """
    # Import lazily so server can still start even if dependency isn't installed.
    try:
        from sqlglot import parse_one, exp  # type: ignore
    except ImportError as exc:
        raise ImportError("sqlglot is required for production-grade SQL validation.") from exc

    # Try duckdb dialect first; if unsupported in a given sqlglot version,
    # fall back to postgres-like parsing.
    try:
        ast = parse_one(sql, read="duckdb")
    except Exception:
        ast = parse_one(sql, read="postgres")

    cte_names = {_normalize_identifier(x.alias_or_name) for x in ast.find_all(exp.CTE) if x.alias_or_name}

    tables: set[str] = set()
    for t in ast.find_all(exp.Table):
        # e.g. schema.table => take terminal table identifier
        name = t.name or ""
        name = _normalize_identifier(name)
        if not name:
            continue
        if name in cte_names:
            continue
        tables.add(name)
    return frozenset(tables)


def extract_referenced_tables(sql: str) -> set[str]:
    """
    Best-effort table extraction.

    Uses sqlglot when available; falls back to regex otherwise.
    """
    try:
        return set(_extract_tables_sqlglot(sql))
    except ImportError:
        return _extract_tables_regex(sql)


def validate_sql_allowed_tables(sql: str, allowed_table_names: Iterable[str]) -> None:
    """
    Production-grade (best-effort) SQL validation:
    - read-only SELECT/WITH only
    - single statement only
    - FROM/JOIN referenced tables must be in allowlist
    """
    allowed = _allowed_table_set(allowed_table_names)
    _validate_readonly_select(sql)
    _validate_single_statement(sql)

    referenced = extract_referenced_tables(sql)
    if not referenced:
        # If we can't identify tables, prefer safety and reject.
        raise ValueError("SQL validation failed: no referenced tables could be extracted.")

    disallowed = referenced - allowed
    if disallowed:
        raise ValueError(f"SQL validation failed: disallowed tables referenced: {sorted(disallowed)}")

