from __future__ import annotations

from datetime import timedelta
import random

import pandas as pd


ISSUE_CATALOG = {
    "electronics": [
        ("battery issue", "The battery drains much faster than expected."),
        ("device setup", "The setup steps are confusing and the device will not connect."),
        ("damaged item", "The item arrived damaged and does not power on."),
    ],
    "home": [
        ("missing parts", "The package was missing a key part needed for assembly."),
        ("delivery issue", "The order was delayed and the box arrived in poor condition."),
        ("quality concern", "The material quality does not match the listing."),
    ],
    "apparel": [
        ("size mismatch", "The size runs very differently from the chart."),
        ("wrong item", "I received a different color and style than ordered."),
        ("return request", "I need help with a return and refund for this item."),
    ],
    "beauty": [
        ("skin reaction", "The product caused irritation after first use."),
        ("packaging defect", "The pump is broken and the product leaks."),
        ("refund delay", "My refund request has not been processed yet."),
    ],
}
PRIORITIES = ["low", "medium", "high"]
STATUSES = ["closed", "closed", "closed", "open"]
CHANNELS = ["email", "chat", "web_form"]


def generate_support_tickets(
    orders: pd.DataFrame, products: pd.DataFrame, count: int, seed: int = 42
) -> pd.DataFrame:
    rng = random.Random(seed + 4)
    product_lookup = products.set_index("product_id")[["category"]].to_dict("index")
    sampled_orders = orders.sample(n=min(count, len(orders)), random_state=seed).reset_index(drop=True)
    rows = []

    for idx, order in sampled_orders.iterrows():
        product_id = order["product_id"]
        category = product_lookup[product_id]["category"]
        issue_type, issue_text = rng.choice(ISSUE_CATALOG[category])
        created_ts = pd.to_datetime(order["order_ts"]) + timedelta(days=rng.randint(0, 21))
        is_closed = rng.random() < 0.85
        resolution_hours = round(rng.uniform(2, 96), 2)
        closed_ts = created_ts + timedelta(hours=resolution_hours) if is_closed else pd.NaT
        refund_related = bool(order["refund_flag"])
        csat_floor = 1 if refund_related else 2

        rows.append(
            {
                "ticket_id": f"TKT_{idx + 1:07d}",
                "customer_id": order["customer_id"],
                "product_id": product_id,
                "created_ts": created_ts.isoformat(),
                "closed_ts": None if pd.isna(closed_ts) else closed_ts.isoformat(),
                "issue_type": issue_type,
                "priority": rng.choices(PRIORITIES, weights=[0.25, 0.55, 0.2], k=1)[0],
                "status": "closed" if is_closed else rng.choice(STATUSES),
                "resolution_time_hours": resolution_hours if is_closed else None,
                "csat_score": rng.randint(csat_floor, 5) if is_closed else None,
                "channel": rng.choice(CHANNELS),
                "ticket_text": issue_text,
            }
        )

    return pd.DataFrame(rows)
