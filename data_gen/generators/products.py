from __future__ import annotations

from datetime import datetime, timedelta
import random

import pandas as pd


CATEGORY_MAP = {
    "electronics": ["audio", "wearables", "mobile", "accessories"],
    "home": ["kitchen", "decor", "storage", "furniture"],
    "apparel": ["tops", "bottoms", "footwear", "outerwear"],
    "beauty": ["skincare", "haircare", "makeup", "wellness"],
}
STATUSES = ["active", "active", "active", "discontinued"]


def generate_products(count: int, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed + 1)
    now = datetime.utcnow()
    rows = []

    for idx in range(1, count + 1):
        category = rng.choice(list(CATEGORY_MAP))
        rows.append(
            {
                "product_id": f"PROD_{idx:06d}",
                "product_name": f"{category.title()} Item {idx}",
                "category": category,
                "subcategory": rng.choice(CATEGORY_MAP[category]),
                "base_price": round(rng.uniform(10, 500), 2),
                "launch_ts": (
                    now - timedelta(days=rng.randint(0, 900), hours=rng.randint(0, 23))
                ).isoformat(timespec="seconds"),
                "status": rng.choice(STATUSES),
            }
        )

    return pd.DataFrame(rows)
