from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]


def load_settings() -> dict[str, str]:
    load_dotenv(ROOT / ".env")
    return {
        "duckdb_path": os.environ.get(
            "DUCKDB_PATH", str(ROOT / "data" / "warehouse" / "pulseiq.duckdb")
        ),
        "qdrant_path": os.environ.get("QDRANT_PATH", str(ROOT / "data" / "vector" / "qdrant")),
        "collection_name": os.environ.get("QDRANT_COLLECTION", "support_tickets"),
        "embedding_model": os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
    }
