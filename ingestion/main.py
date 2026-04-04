from __future__ import annotations

from pathlib import Path

import duckdb

from ingestion.loaders.customers import load_customers
from ingestion.loaders.events import load_events
from ingestion.loaders.orders import load_orders
from ingestion.loaders.products import load_products
from ingestion.loaders.tickets import load_tickets


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "data" / "source"
RAW_ROOT = ROOT / "data" / "raw"
WAREHOUSE_PATH = ROOT / "data" / "warehouse" / "pulseiq.duckdb"


def register_raw_tables() -> None:
    WAREHOUSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(WAREHOUSE_PATH))
    try:
        con.execute(
            f"""
            create or replace table raw_customers as
            select * from read_parquet('{RAW_ROOT / "customers" / "customers.parquet"}')
            """
        )
        con.execute(
            f"""
            create or replace table raw_products as
            select * from read_parquet('{RAW_ROOT / "products" / "products.parquet"}')
            """
        )
        con.execute(
            f"""
            create or replace table raw_orders as
            select * from read_parquet('{RAW_ROOT / "orders" / "orders.parquet"}')
            """
        )
        con.execute(
            f"""
            create or replace table raw_events as
            select * from read_parquet('{RAW_ROOT / "events" / "events.parquet"}')
            """
        )
        con.execute(
            f"""
            create or replace table raw_support_tickets as
            select * from read_parquet('{RAW_ROOT / "support_tickets" / "support_tickets.parquet"}')
            """
        )
    finally:
        con.close()


def main() -> None:
    load_customers(
        SOURCE_ROOT / "customers" / "customers.csv",
        RAW_ROOT / "customers" / "customers.parquet",
    )
    load_products(
        SOURCE_ROOT / "products" / "products.csv",
        RAW_ROOT / "products" / "products.parquet",
    )
    load_orders(
        SOURCE_ROOT / "orders" / "orders.csv",
        RAW_ROOT / "orders" / "orders.parquet",
    )
    load_events(
        SOURCE_ROOT / "events" / "events.jsonl",
        RAW_ROOT / "events" / "events.parquet",
    )
    load_tickets(
        SOURCE_ROOT / "support_tickets" / "support_tickets.csv",
        RAW_ROOT / "support_tickets" / "support_tickets.parquet",
    )
    register_raw_tables()
    print("Raw ingestion completed successfully and DuckDB raw tables are ready.")


if __name__ == "__main__":
    main()
