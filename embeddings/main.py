from __future__ import annotations

from pathlib import Path

from embeddings.config import load_settings
from embeddings.indexer import index_support_tickets


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = load_settings()
    duckdb_path = settings["duckdb_path"]
    qdrant_path = settings["qdrant_path"]
    collection_name = settings["collection_name"]
    embedding_model = settings["embedding_model"]

    Path(qdrant_path).mkdir(parents=True, exist_ok=True)
    index_support_tickets(
        duckdb_path=duckdb_path,
        qdrant_path=qdrant_path,
        collection_name=collection_name,
        embedding_model=embedding_model,
    )
    print(f"Indexed support tickets into Qdrant collection '{collection_name}'.")


if __name__ == "__main__":
    main()
