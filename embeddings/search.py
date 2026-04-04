from __future__ import annotations

import argparse

from embeddings.config import load_settings
from embeddings.query import search_support_tickets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search support ticket embeddings.")
    parser.add_argument("query", help="Natural-language query to search for")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to return")
    parser.add_argument("--product-id", dest="product_id")
    parser.add_argument("--category")
    parser.add_argument("--issue-type", dest="issue_type")
    parser.add_argument("--priority")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    filters = {
        "product_id": args.product_id,
        "category": args.category,
        "issue_type": args.issue_type,
        "priority": args.priority,
    }
    results = search_support_tickets(
        query_text=args.query,
        qdrant_path=settings["qdrant_path"],
        collection_name=settings["collection_name"],
        embedding_model=settings["embedding_model"],
        limit=args.limit,
        filters=filters,
    )

    if not results:
        print("No matching ticket chunks found.")
        return

    for idx, result in enumerate(results, start=1):
        print(f"[{idx}] score={result['score']:.4f} ticket_id={result['ticket_id']}")
        print(
            f"    product={result['product_name']} category={result['category']} "
            f"issue_type={result['issue_type']} priority={result['priority']} "
            f"created_date={result['created_date']}"
        )
        print(f"    text={result['text']}")


if __name__ == "__main__":
    main()
