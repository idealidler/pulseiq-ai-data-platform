from __future__ import annotations

from datetime import datetime, timedelta
import json
import random

import pandas as pd


EVENT_TYPES = [
    ("page_view", 0.35),
    ("product_view", 0.25),
    ("add_to_cart", 0.15),
    ("checkout_start", 0.08),
    ("purchase", 0.07),
    ("search", 0.08),
    ("support_page_view", 0.02),
]
DEVICES = ["mobile", "desktop", "tablet"]
TRAFFIC_SOURCES = ["organic", "paid_search", "email", "social", "direct"]
PAGES = ["home", "search", "product_detail", "cart", "checkout", "support"]


def generate_events(
    customers: pd.DataFrame, products: pd.DataFrame, count: int, seed: int = 42
) -> pd.DataFrame:
    rng = random.Random(seed + 3)
    now = datetime.utcnow()
    customer_ids = customers["customer_id"].tolist()
    product_ids = products["product_id"].tolist()
    weighted_event_types = [event for event, _ in EVENT_TYPES]
    weights = [weight for _, weight in EVENT_TYPES]
    rows = []

    for idx in range(1, count + 1):
        event_type = rng.choices(weighted_event_types, weights=weights, k=1)[0]
        event_ts = now - timedelta(days=rng.randint(0, 180), minutes=rng.randint(0, 1440))
        page_name = "support" if event_type == "support_page_view" else rng.choice(PAGES)
        metadata = {
            "campaign_id": f"CMP_{rng.randint(1, 50):03d}",
            "feature_name": rng.choice(["recommendations", "search", "checkout", "reviews"]),
            "referrer": rng.choice(["google", "newsletter", "instagram", "direct"]),
        }
        rows.append(
            {
                "event_id": f"EVT_{idx:09d}",
                "customer_id": rng.choice(customer_ids),
                "session_id": f"SES_{rng.randint(1, max(1, count // 4)):08d}",
                "event_ts": event_ts.isoformat(timespec="seconds"),
                "event_type": event_type,
                "product_id": rng.choice(product_ids),
                "page_name": page_name,
                "device_type": rng.choice(DEVICES),
                "traffic_source": rng.choice(TRAFFIC_SOURCES),
                "metadata_json": json.dumps(metadata),
            }
        )

    return pd.DataFrame(rows)
