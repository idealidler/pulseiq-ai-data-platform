from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DBT_SCHEMA_PATH = ROOT / "dbt" / "models" / "schema.yml"


def _load_schema_file() -> dict[str, Any]:
    return yaml.safe_load(DBT_SCHEMA_PATH.read_text()) or {}


def _column_summary(columns: list[dict[str, Any]], limit: int = 8) -> str:
    selected = []
    for column in columns[:limit]:
        name = column.get("name")
        description = column.get("description")
        if not name or not description:
            continue
        selected.append(f"{name}: {description}")
    return "; ".join(selected)


@lru_cache(maxsize=1)
def get_assistant_schema_context() -> dict[str, Any]:
    schema = _load_schema_file()
    models: list[dict[str, Any]] = schema.get("models", [])

    allowed_models: list[dict[str, Any]] = []
    for model in models:
        meta = (model.get("meta") or {}).get("ai_hint") or {}
        role = meta.get("role")
        if role not in {"serving", "dimension"}:
            continue
        allowed_models.append(model)

    allowed_table_names = [str(model["name"]) for model in allowed_models if model.get("name")]

    lines = [
        "## Assistant schema context",
        "The following table semantics come from dbt model metadata and are the source of truth for business meaning.",
    ]

    for model in allowed_models:
        meta = (model.get("meta") or {}).get("ai_hint") or {}
        name = model["name"]
        description = model.get("description", "")
        grain = meta.get("grain", "")
        use_for = meta.get("use_for", "")
        best_for = meta.get("best_for", [])
        primary_metrics = meta.get("primary_metrics", [])
        primary_dimensions = meta.get("primary_dimensions", [])
        default_business_interpretation = meta.get("default_business_interpretation", {})
        column_summary = _column_summary(model.get("columns", []))

        lines.append(f"- {name}")
        if description:
            lines.append(f"  - purpose: {description}")
        if grain:
            lines.append(f"  - grain: {grain}")
        if use_for:
            lines.append(f"  - use_for: {use_for}")
        if best_for:
            lines.append(f"  - best_for: {', '.join(best_for)}")
        if primary_dimensions:
            lines.append(f"  - key_dimensions: {', '.join(primary_dimensions)}")
        if primary_metrics:
            lines.append(f"  - key_metrics: {', '.join(primary_metrics)}")
        if default_business_interpretation:
            defaults = ", ".join(f"{k} -> {v}" for k, v in default_business_interpretation.items())
            lines.append(f"  - defaults: {defaults}")
        if column_summary:
            lines.append(f"  - columns: {column_summary}")

    return {
        "allowed_table_names": allowed_table_names,
        "prompt_block": "\n".join(lines).strip(),
    }


def build_sql_tool_definition() -> dict[str, Any]:
    context = get_assistant_schema_context()
    allowed = ", ".join(context["allowed_table_names"])
    return {
        "type": "function",
        "name": "run_sql_query",
        "description": f"Run read-only SQL against DuckDB. Only use these tables: {allowed}.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": f"A SELECT query using only these existing tables: {allowed}.",
                }
            },
            "required": ["sql"],
            "additionalProperties": False,
        },
    }
