import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from loader import load_and_chunk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.embeddings import DashScopeEmbeddings

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://115.190.125.94:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY","root")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "helpdesk-knowledge")

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")


def main():
    if not DASHSCOPE_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY must be set in your .env file.")

    docs = load_and_chunk(data_dir="../data")
    texts = [c for c, _ in docs]
    metadatas = [m for _, m in docs]

    embeddings = DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
    )

    QdrantVectorStore.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        collection_name=QDRANT_COLLECTION,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )
    print(
        f"Ingested {len(texts)} chunks into Qdrant collection "
        f"{QDRANT_COLLECTION} at {QDRANT_URL}"
    )


if __name__ == "__main__":
    main()
