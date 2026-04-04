from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd


def load_tickets(source_path: Path, target_path: Path) -> None:
    df = pd.read_csv(source_path)
    df["created_date"] = pd.to_datetime(df["created_ts"]).dt.date.astype(str)
    df["ingested_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    df["source_file"] = source_path.name
    df["load_date"] = date.today().isoformat()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(target_path, index=False)
