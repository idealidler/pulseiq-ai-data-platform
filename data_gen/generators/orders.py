from __future__ import annotations

from datetime import datetime, timedelta
import random

import pandas as pd


PAYMENT_METHODS = ["card", "paypal", "bank_transfer", "wallet"]


def generate_orders(
    customers: pd.DataFrame, products: pd.DataFrame, count: int, seed: int = 42
) -> pd.DataFrame:
    rng = random.Random(seed + 2)
    now = datetime.utcnow()
    customer_ids = customers["customer_id"].tolist()
    product_records = products[["product_id", "base_price"]].to_dict("records")
    rows = []

    for idx in range(1, count + 1):
        product = rng.choice(product_records)
        quantity = rng.randint(1, 5)
        unit_price = float(product["base_price"])
        gross_amount = round(quantity * unit_price, 2)
        discount_amount = round(gross_amount * rng.choice([0, 0, 0.05, 0.1, 0.15]), 2)
        net_amount = round(gross_amount - discount_amount, 2)
        refund_flag = rng.random() < 0.08
        refund_amount = round(net_amount * rng.uniform(0.25, 1.0), 2) if refund_flag else 0.0

        rows.append(
            {
                "order_line_id": f"OL_{idx:08d}",
                "order_id": f"ORD_{((idx - 1) // rng.randint(1, 3)) + 1:07d}",
                "customer_id": rng.choice(customer_ids),
                "product_id": product["product_id"],
                "order_ts": (
                    now - timedelta(days=rng.randint(0, 365), hours=rng.randint(0, 23))
                ).isoformat(timespec="seconds"),
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_amount": discount_amount,
                "gross_amount": gross_amount,
                "net_amount": net_amount,
                "refund_flag": refund_flag,
                "refund_amount": refund_amount,
                "payment_method": rng.choice(PAYMENT_METHODS),
            }
        )

    return pd.DataFrame(rows)
