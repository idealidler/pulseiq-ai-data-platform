import json
import os
import sys
import uuid
from pathlib import Path

# 1. Resolve the root path FIRST
ROOT_DIR = Path(__file__).resolve().parents[1]

# 2. Add the root path to Python's system path so it can find 'embeddings'
sys.path.append(str(ROOT_DIR))

# 3. NOW you can safely import your internal modules
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from embeddings.config import load_settings


def seed_golden_dataset():
    data_path = ROOT_DIR / "data" / "golden_sql.json"
    
    settings = load_settings()
    # 1. Initialize Clients
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required to generate embeddings.")
    
    openai_client = OpenAI(api_key=api_key)
    
    qdrant_client = QdrantClient(path=settings["qdrant_path"])
    
    collection_name = "sql_examples"

    # 2. Load the Golden Dataset
    if not data_path.exists():
        raise FileNotFoundError(f"Could not find golden dataset at {data_path}")
        
    with open(data_path, "r") as f:
        golden_data = json.load(f)

    questions = [item["question"] for item in golden_data]
    print(f"Loaded {len(questions)} questions from golden_sql.json")

    # 3. Generate Embeddings for the Questions
    print("Generating embeddings via OpenAI for golden SQL dataset...")
    # Using text-embedding-3-small as the modern default, adjust if you use a different one
    response = openai_client.embeddings.create(
        input=questions,
        model="text-embedding-3-small"
    )
    
    embeddings = [data.embedding for data in response.data]
    vector_size = len(embeddings[0])

    # 4. Recreate the Collection (This wipes old data if you rerun the script)
    print(f"Creating Qdrant collection '{collection_name}' with vector size {vector_size}...")
    if qdrant_client.collection_exists(collection_name):
        qdrant_client.delete_collection(collection_name)
        
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    # 5. Build the Points and Upsert
    points = []
    for idx, item in enumerate(golden_data):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),  # Generate a unique ID for each record
                vector=embeddings[idx],
                payload={
                    "question": item["question"],
                    "sql": item["sql"]
                }
            )
        )

    print(f"Uploading {len(points)} points to Qdrant...")
    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )
    
    print("✅ Golden dataset successfully seeded into Qdrant.")


if __name__ == "__main__":
    seed_golden_dataset()