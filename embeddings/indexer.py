from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from embeddings.chunking import chunk_text
from embeddings.data_source import load_ticket_rows


def build_payloads(duckdb_path: str | Path) -> list[dict[str, Any]]:
    df = load_ticket_rows(duckdb_path)
    payloads: list[dict[str, Any]] = []

    for row in df.to_dict("records"):
        chunks = chunk_text(row["ticket_text"])
        for idx, chunk in enumerate(chunks):
            payloads.append(
                {
                    "chunk_key": f'{row["ticket_id"]}_chunk_{idx}',
                    "text": chunk,
                    "metadata": {
                        "chunk_key": f'{row["ticket_id"]}_chunk_{idx}',
                        "ticket_id": row["ticket_id"],
                        "created_date": str(row["created_date"]),
                        "customer_id": row["customer_id"],
                        "region": row["region"],
                        "segment": row["segment"],
                        "product_id": row["product_id"],
                        "product_name": row["product_name"],
                        "category": row["category"],
                        "subcategory": row["subcategory"],
                        "issue_type": row["issue_type"],
                        "priority": row["priority"],
                        "status": row["status"],
                        "channel": row["channel"],
                    },
                }
            )
    return payloads


def embed_texts(client: OpenAI, model: str, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]


def index_support_tickets(
    duckdb_path: str | Path,
    qdrant_path: str | Path,
    collection_name: str,
    embedding_model: str,
    batch_size: int = 128,
) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required to build embeddings.")

    payloads = build_payloads(duckdb_path)
    if not payloads:
        raise ValueError("No ticket text rows found to index.")

    openai_client = OpenAI(api_key=api_key)
    qdrant_client = QdrantClient(path=str(qdrant_path))

    first_vector = embed_texts(openai_client, embedding_model, [payloads[0]["text"]])[0]
    qdrant_client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=len(first_vector), distance=Distance.COSINE),
    )

    for start in range(0, len(payloads), batch_size):
        batch = payloads[start : start + batch_size]
        vectors = embed_texts(openai_client, embedding_model, [item["text"] for item in batch])
        points = [
            PointStruct(
                id=start + offset + 1,
                vector=vector,
                payload={**item["metadata"], "text": item["text"]},
            )
            for offset, (item, vector) in enumerate(zip(batch, vectors, strict=True))
        ]
        qdrant_client.upsert(collection_name=collection_name, points=points)
