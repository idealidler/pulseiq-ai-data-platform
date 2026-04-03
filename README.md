# PulseIQ

Milestone 1 builds the first working slice of the platform:

- Generate synthetic `customers`, `products`, and `orders` source data
- Ingest those files into raw Parquet datasets
- Transform them with dbt into staging models and a first revenue mart

## Run

1. Install dependencies
2. Run `python data_gen/main.py`
3. Run `python ingestion/main.py`
4. Run `dbt build --project-dir dbt --profiles-dir dbt`

## Outputs

- Source CSVs under `data/source/`
- Raw Parquet datasets under `data/raw/`
- DuckDB warehouse at `data/warehouse/pulseiq.duckdb`
- Raw DuckDB tables: `raw_customers`, `raw_products`, `raw_orders`
