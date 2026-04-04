from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from embeddings.indexer import embed_texts


def _build_filter(filters: dict[str, str] | None) -> Filter | None:
    if not filters:
        return None

    conditions = [
        FieldCondition(key=key, match=MatchValue(value=value))
        for key, value in filters.items()
        if value is not None and value != ""
    ]
    return Filter(must=conditions) if conditions else None


def search_support_tickets(
    query_text: str,
    qdrant_path: str | Path,
    collection_name: str,
    embedding_model: str,
    limit: int = 5,
    filters: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required to query embeddings.")

    openai_client = OpenAI(api_key=api_key)
    qdrant_client = QdrantClient(path=str(qdrant_path))
    query_vector = embed_texts(openai_client, embedding_model, [query_text])[0]
    search_filter = _build_filter(filters)

    hits = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=search_filter,
        limit=limit,
        with_payload=True,
    ).points

    results: list[dict[str, Any]] = []
    for hit in hits:
        payload = hit.payload or {}
        results.append(
            {
                "score": hit.score,
                "ticket_id": payload.get("ticket_id"),
                "chunk_key": payload.get("chunk_key"),
                "product_id": payload.get("product_id"),
                "product_name": payload.get("product_name"),
                "category": payload.get("category"),
                "issue_type": payload.get("issue_type"),
                "priority": payload.get("priority"),
                "created_date": payload.get("created_date"),
                "text": payload.get("text"),
            }
        )
    return results
