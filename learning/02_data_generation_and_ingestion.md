# Chapter 2: Data Generation and Ingestion

## Why this project generates its own data

This project does not depend on a public production dataset.

Instead, it generates synthetic business data so the system can:

- control scale
- control schema shape
- model cross-table relationships
- simulate realistic support and refund behavior
- safely demonstrate architecture

## Data generation layer

The generation layer creates source-style files for:

- customers
- products
- orders
- events
- support tickets

These files simulate upstream systems.

That means they should be thought of as "source data", not as warehouse-ready tables.

## What ingestion does

Ingestion moves source data into the platform.

It does not do deep business transformations.

Its main responsibilities are:

- read source CSV or JSONL
- add ingestion metadata
- write Parquet into the raw layer
- register raw tables in DuckDB

Metadata added during ingestion includes things like:

- ingestion timestamp
- source file
- load date

This makes data easier to trace and audit later.

## Why Parquet is used

Parquet is the raw/bronze storage format in this project.

It is used because:

- it is columnar
- it compresses well
- it is fast for analytics engines like DuckDB
- it is better suited than CSV for downstream querying

So the ingestion flow is:

- source CSV or JSONL
- raw Parquet
- raw DuckDB tables

## Why DuckDB is introduced here

DuckDB is the local analytical engine for the project.

It acts like the warehouse.

After ingestion:

- Parquet files remain the storage layer
- DuckDB becomes the query and transformation layer

dbt then runs on top of DuckDB.

## Main idea to understand

Source data is not yet trustworthy enough for direct analytics or AI.

Ingestion creates a controlled landing point so the rest of the pipeline can work from a consistent raw layer.

Referenced files:

- [data_gen/main.py](/Users/akshayjain/Documents/chat_bot/data_gen/main.py)
- [ingestion/main.py](/Users/akshayjain/Documents/chat_bot/ingestion/main.py)
- [ingestion/loaders/orders.py](/Users/akshayjain/Documents/chat_bot/ingestion/loaders/orders.py)
