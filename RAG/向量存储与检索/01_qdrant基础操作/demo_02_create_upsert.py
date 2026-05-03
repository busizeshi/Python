import os
import uuid

import dashscope
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


QDRANT_URL = os.getenv("QDRANT_URL", "http://115.190.125.94/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY","root")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "qdrant_basic_demo")
QWEN_EMBEDDING_MODEL = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")


def embed_texts(texts: list[str]) -> list[list[float]]:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("Please set DASHSCOPE_API_KEY")

    dashscope.api_key = api_key
    resp = dashscope.TextEmbedding.call(model=QWEN_EMBEDDING_MODEL, input=texts)
    if resp.status_code != 200:
        raise RuntimeError(f"Embedding failed: {resp}")

    vectors: list[list[float]] = []
    for item in resp.output["embeddings"]:
        vectors.append(item["embedding"])
    return vectors


if __name__ == "__main__":
    texts = [
        "Qdrant is a vector database for semantic search.",
        "Hybrid retrieval combines dense and sparse signals.",
        "Multimodal retrieval can search images with text.",
        "Qwen embedding model converts text into vectors.",
    ]

    payloads = [
        {"category": "qdrant", "source": "note_a"},
        {"category": "hybrid", "source": "note_b"},
        {"category": "multimodal", "source": "note_c"},
        {"category": "embedding", "source": "note_d"},
    ]

    vectors = embed_texts(texts)
    vector_size = len(vectors[0])

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    if client.collection_exists(collection_name=COLLECTION_NAME):
        client.delete_collection(collection_name=COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    points = []
    for text, vector, payload in zip(texts, vectors, payloads):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"text": text, **payload},
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Collection ready: {COLLECTION_NAME}")
    print(f"Inserted points: {len(points)}")
    print(f"Vector dim: {vector_size}")
