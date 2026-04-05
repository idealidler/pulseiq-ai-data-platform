# Chapter 4: Semantic Layer and Schema Context

## Why semantic meaning matters

An AI assistant does not just need table names.
It needs to understand:

- what each model represents
- what grain the table uses
- what metrics are meaningful in that table
- which table is appropriate for which kind of question

If this meaning only lives in a handwritten prompt, the system becomes brittle.

## Where the semantic meaning lives in this project

The canonical meaning lives in dbt model metadata inside:

- `dbt/models/schema.yml`

This file now includes:

- model descriptions
- column descriptions
- `meta.ai_hint`

## What `meta.ai_hint` does

`meta.ai_hint` is a compact AI-facing metadata block added to models.

It includes fields like:

- `role`
- `grain`
- `use_for`
- `best_for`
- `primary_dimensions`
- `primary_metrics`

This is useful because it captures how the table should be used by the assistant without turning dbt YAML into a prompt dump.

## Why this is better than hardcoding everything in the prompt

If the prompt contains the full semantic layer manually:

- the prompt can drift from the dbt models
- schema changes become harder to maintain
- business meaning gets duplicated

By keeping semantics in dbt:

- the data platform stays the source of truth
- the AI context is derived from the data platform

## How runtime schema context is generated

This project uses:

- `api/services/schema_context.py`

This module:

1. reads `dbt/models/schema.yml`
2. selects AI-relevant models
3. builds a compact schema summary
4. builds the SQL tool definition dynamically

So the assistant now receives schema context from dbt metadata rather than from a hand-maintained table list.

## Why this is a major architectural improvement

This change improves:

- maintainability
- semantic consistency
- prompt cleanliness
- production readiness

It also means that improving dbt metadata improves the assistant.

Referenced files:

- [dbt/models/schema.yml](/Users/akshayjain/Documents/chat_bot/dbt/models/schema.yml)
- [api/services/schema_context.py](/Users/akshayjain/Documents/chat_bot/api/services/schema_context.py)
