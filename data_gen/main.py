from __future__ import annotations

from pathlib import Path

from data_gen.generators.customers import generate_customers
from data_gen.generators.events import generate_events
from data_gen.generators.orders import generate_orders
from data_gen.generators.products import generate_products
from data_gen.generators.tickets import generate_support_tickets


ROOT = Path(__file__).resolve().parents[1]
DATA_SOURCE = ROOT / "data" / "source"


def main() -> None:
    (DATA_SOURCE / "customers").mkdir(parents=True, exist_ok=True)
    (DATA_SOURCE / "events").mkdir(parents=True, exist_ok=True)
    (DATA_SOURCE / "products").mkdir(parents=True, exist_ok=True)
    (DATA_SOURCE / "orders").mkdir(parents=True, exist_ok=True)
    (DATA_SOURCE / "support_tickets").mkdir(parents=True, exist_ok=True)

    customers = generate_customers(count=5_000)
    products = generate_products(count=500)
    orders = generate_orders(customers=customers, products=products, count=100_000)
    events = generate_events(customers=customers, products=products, count=500_000)
    support_tickets = generate_support_tickets(orders=orders, products=products, count=15_000)

    customers.to_csv(DATA_SOURCE / "customers" / "customers.csv", index=False)
    events.to_json(DATA_SOURCE / "events" / "events.jsonl", orient="records", lines=True)
    products.to_csv(DATA_SOURCE / "products" / "products.csv", index=False)
    orders.to_csv(DATA_SOURCE / "orders" / "orders.csv", index=False)
    support_tickets.to_csv(
        DATA_SOURCE / "support_tickets" / "support_tickets.csv", index=False
    )

    print("Synthetic source data generated successfully.")


if __name__ == "__main__":
    main()
