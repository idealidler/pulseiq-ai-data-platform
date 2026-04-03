from __future__ import annotations

from datetime import datetime, timedelta
import random

import pandas as pd


REGIONS = ["North", "South", "East", "West"]
COUNTRIES = ["USA", "Canada"]
SEGMENTS = ["consumer", "small_business", "enterprise"]
CHANNELS = ["organic", "paid_search", "email", "partner", "social"]


def generate_customers(count: int, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    now = datetime.utcnow()
    rows = []

    for idx in range(1, count + 1):
        signup_offset_days = rng.randint(0, 730)
        signup_ts = now - timedelta(days=signup_offset_days, hours=rng.randint(0, 23))
        rows.append(
            {
                "customer_id": f"CUST_{idx:06d}",
                "signup_ts": signup_ts.isoformat(timespec="seconds"),
                "region": rng.choice(REGIONS),
                "country": rng.choice(COUNTRIES),
                "segment": rng.choices(SEGMENTS, weights=[0.75, 0.2, 0.05], k=1)[0],
                "acquisition_channel": rng.choice(CHANNELS),
                "is_active": rng.choices([True, False], weights=[0.9, 0.1], k=1)[0],
            }
        )

    return pd.DataFrame(rows)
