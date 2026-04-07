from __future__ import annotations

import sys
from pathlib import Path

from embeddings.config import load_settings
from embeddings.indexer import index_support_tickets
from ingestion.seed_qdrant import seed_golden_dataset


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    settings = load_settings()
    duckdb_path = settings["duckdb_path"]
    qdrant_path = settings["qdrant_path"]
    collection_name = settings["collection_name"]
    embedding_model = settings["embedding_model"]

    Path(qdrant_path).mkdir(parents=True, exist_ok=True)
    
    # Index support tickets
    index_support_tickets(
        duckdb_path=duckdb_path,
        qdrant_path=qdrant_path,
        collection_name=collection_name,
        embedding_model=embedding_model,
    )
    print(f"Indexed support tickets into Qdrant collection '{collection_name}'.")
    
    # Seed golden SQL dataset
    try:
        seed_golden_dataset()
    except Exception as e:
        print(f"⚠️  Warning: Failed to seed golden dataset: {e}")


if __name__ == "__main__":
    main()
