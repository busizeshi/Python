import os

import dashscope
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue


QDRANT_URL = os.getenv("QDRANT_URL", "http://115.190.125.94/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "root")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "qdrant_basic_demo")
QWEN_EMBEDDING_MODEL = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")


def embed_query(text: str) -> list[float]:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("Please set DASHSCOPE_API_KEY")

    dashscope.api_key = api_key
    resp = dashscope.TextEmbedding.call(model=QWEN_EMBEDDING_MODEL, input=text)
    if resp.status_code != 200:
        raise RuntimeError(f"Embedding failed: {resp}")

    return resp.output["embeddings"][0]["embedding"]


if __name__ == "__main__":
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    query = "How to use Qdrant for semantic retrieval?"
    query_vector = embed_query(query)

    print("=== Vector Search Top 3 ===")
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=3,
        with_payload=True,
    )
    hits = response.points
    for i, hit in enumerate(hits, start=1):
        print(f"{i}. score={hit.score:.4f}, category={hit.payload.get('category')}, text={hit.payload.get('text')}")

    print("\n=== Filtered Search (category=qdrant) ===")
    filtered_response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="category",
                    match=MatchValue(value="qdrant"),
                )
            ]
        ),
        limit=3,
        with_payload=True,
    )
    filtered_hits = filtered_response.points
    for i, hit in enumerate(filtered_hits, start=1):
        print(f"{i}. score={hit.score:.4f}, category={hit.payload.get('category')}, text={hit.payload.get('text')}")
