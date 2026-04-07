from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue


@lru_cache(maxsize=1)
def _get_openai_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, timeout=20.0, max_retries=1)


@lru_cache(maxsize=2)
def _get_qdrant_client(qdrant_path: str) -> QdrantClient:
    return QdrantClient(path=qdrant_path)


def _build_filter(filters: dict[str, str] | None) -> Filter | None:
    if not filters:
        return None

    conditions = [
        FieldCondition(key=key, match=MatchValue(value=value))
        for key, value in filters.items()
        if value is not None and value != ""
    ]
    return Filter(must=conditions) if conditions else None


@lru_cache(maxsize=4096)
def _embed_single_text_cached(embedding_model: str, text: str) -> tuple[float, ...]:
    """
    Cache OpenAI embedding vectors for identical (model, text) pairs.

    This is critical for hybrid queries where we run many Qdrant searches with the
    same semantic query text but different metadata filters.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required to query embeddings.")

    normalized = (text or "").strip()
    if not normalized:
        raise ValueError("query_text must be a non-empty string.")

    openai_client = _get_openai_client(api_key)
    response = openai_client.embeddings.create(model=embedding_model, input=[normalized])
    if not response.data:
        raise ValueError("OpenAI embeddings returned no data.")
    return tuple(response.data[0].embedding)


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

    safe_limit = max(1, min(limit, 3))
    qdrant_client = _get_qdrant_client(str(qdrant_path))
    # Embed once per (model, query_text); cached across repeated filtered searches.
    query_vector = list(_embed_single_text_cached(embedding_model, query_text))
    search_filter = _build_filter(filters)

    hits = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=search_filter,
        limit=safe_limit,
        with_payload=True,
    ).points

    results: list[dict[str, Any]] = []
    for hit in hits:
        payload = hit.payload or {}
        # Extract all payload fields (supports both support_tickets and sql_examples collections)
        result_item = {"score": hit.score}
        result_item.update(payload)
        results.append(result_item)
    return results
