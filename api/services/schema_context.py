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
def get_allowed_models() -> list[dict[str, Any]]:
    """Caches and returns only the serving/dimension models."""
    schema = _load_schema_file()
    models: list[dict[str, Any]] = schema.get("models", [])
    
    allowed_models = []
    for model in models:
        meta = (model.get("meta") or {}).get("ai_hint") or {}
        role = meta.get("role")
        if role in {"serving", "dimension"}:
            allowed_models.append(model)
            
    return allowed_models

def get_schema_catalog() -> dict[str, str]:
    """Returns a lightweight dictionary of table_name: description for the LLM Router."""
    models = get_allowed_models()
    return {
        str(model["name"]): str(model.get("description", "No description provided."))
        for model in models if model.get("name")
    }

def get_specific_schema_context(selected_tables: list[str]) -> dict[str, Any]:
    """Generates the heavy prompt block ONLY for the selected tables."""
    all_models = get_allowed_models()
    
    # Filter to only the tables the LLM requested (plus dimensions if needed, though 
    # a smart LLM will pick the dimensions too)
    target_models = [m for m in all_models if m.get("name") in selected_tables]
    
    if not target_models:
        # Fallback just in case the router hallucinates or finds nothing
        return {"allowed_table_names": [], "prompt_block": "No relevant tables selected."}

    allowed_table_names = [str(m["name"]) for m in target_models]
    
    lines = [
        "## Assistant schema context",
        "The following table semantics come from dbt model metadata and are the source of truth for business meaning.",
    ]

    for model in target_models:
        meta = (model.get("meta") or {}).get("ai_hint") or {}
        name = model["name"]
        
        lines.append(f"- {name}")
        if description := model.get("description"):
            lines.append(f"  - purpose: {description}")
        if grain := meta.get("grain"):
            lines.append(f"  - grain: {grain}")
        if use_for := meta.get("use_for"):
            lines.append(f"  - use_for: {use_for}")
        if best_for := meta.get("best_for"):
            lines.append(f"  - best_for: {', '.join(best_for)}")
        if primary_metrics := meta.get("primary_metrics"):
            lines.append(f"  - key_metrics: {', '.join(primary_metrics)}")
        if primary_dimensions := meta.get("primary_dimensions"):
            lines.append(f"  - key_dimensions: {', '.join(primary_dimensions)}")
        if default_business_interpretation := meta.get("default_business_interpretation"):
            defaults = ", ".join(f"{k} -> {v}" for k, v in default_business_interpretation.items())
            lines.append(f"  - defaults: {defaults}")
        if column_summary := _column_summary(model.get("columns", [])):
            lines.append(f"  - columns: {column_summary}")

    return {
        "allowed_table_names": allowed_table_names,
        "prompt_block": "\n".join(lines).strip(),
    }

def build_sql_tool_definition(allowed_table_names: list[str]) -> dict[str, Any]:
    """Dynamically builds the SQL tool definition based on selected tables."""
    allowed = ", ".join(allowed_table_names) if allowed_table_names else "none"
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