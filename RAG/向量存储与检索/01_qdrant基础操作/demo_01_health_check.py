import os

from qdrant_client import QdrantClient


QDRANT_URL = os.getenv("QDRANT_URL", "http://115.190.125.94/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY","root")


if __name__ == "__main__":
    if not QDRANT_API_KEY:
        raise RuntimeError("QDRANT_API_KEY is not set. Please export your Qdrant API key.")

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    collections = client.get_collections()
    print(f"Qdrant connected: {QDRANT_URL}")
    print(f"Collection count: {len(collections.collections)}")
