from __future__ import annotations

from pathlib import Path
from typing import Any

from embeddings.query import search_support_tickets


def run_vector_search(
    query_text: str,
    qdrant_path: str | Path,
    collection_name: str,
    embedding_model: str,
    limit: int = 3,
    filters: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    return search_support_tickets(
        query_text=query_text,
        qdrant_path=qdrant_path,
        collection_name=collection_name,
        embedding_model=embedding_model,
        limit=max(1, min(limit, 3)),
        filters=filters,
    )
