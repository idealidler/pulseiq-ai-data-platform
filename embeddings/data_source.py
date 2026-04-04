from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def load_ticket_rows(duckdb_path: str | Path) -> pd.DataFrame:
    query = """
        select
            ticket_id,
            created_date,
            customer_id,
            region,
            segment,
            product_id,
            product_name,
            category,
            subcategory,
            issue_type,
            priority,
            status,
            channel,
            coalesce(ticket_text, '') as ticket_text
        from fct_support_tickets_enriched
        where ticket_text is not null
    """
    con = duckdb.connect(str(duckdb_path), read_only=True)
    try:
        return con.execute(query).fetch_df()
    finally:
        con.close()
