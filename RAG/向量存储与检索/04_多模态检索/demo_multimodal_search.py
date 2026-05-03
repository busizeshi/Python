import os
import uuid

import dashscope
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


# -----------------------------
# 全局配置
# -----------------------------
QDRANT_URL = os.getenv("QDRANT_URL", "http://115.190.125.94/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "root")
QWEN_EMBEDDING_MODEL = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")
COLLECTION_NAME = os.getenv("QDRANT_MULTIMODAL_COLLECTION", "qdrant_multimodal_demo")


def embed_texts(texts: list[str], batch_size: int = 10) -> list[list[float]]:
    """调用千问 embedding，按批次生成向量。"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("Please set DASHSCOPE_API_KEY")

    dashscope.api_key = api_key
    vectors: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = dashscope.TextEmbedding.call(model=QWEN_EMBEDDING_MODEL, input=batch)
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding failed: {resp}")
        vectors.extend([item["embedding"] for item in resp.output["embeddings"]])

    return vectors


def build_multimodal_samples() -> list[dict]:
    """
    构造多模态样本。

    说明：
    - text_caption: 用于文本模态向量（描述文本语义）
    - image_caption: 教学中用“图像描述文本”来近似图像模态向量
      真实项目应替换为真正图像 embedding 模型输出。
    """
    return [
        {
            "object_id": "img_001",
            "category": "宠物",
            "text_caption": "一只橘猫趴在木桌上打盹，阳光从窗边照进来。",
            "image_caption": "橘色短毛猫，室内木桌，暖色阳光，安静休息场景。",
        },
        {
            "object_id": "img_002",
            "category": "风景",
            "text_caption": "雪山下有一片湖泊，湖面倒映着蓝天和山峰。",
            "image_caption": "高山雪峰，湖面倒影，蓝天白云，广角自然风光。",
        },
        {
            "object_id": "img_003",
            "category": "美食",
            "text_caption": "一碗牛肉拉面，上面有葱花和半颗溏心蛋。",
            "image_caption": "日式拉面特写，牛肉片，溏心蛋，热气腾腾。",
        },
        {
            "object_id": "img_004",
            "category": "城市",
            "text_caption": "夜晚城市街道霓虹闪烁，路面有雨后反光。",
            "image_caption": "城市夜景，霓虹灯，湿润路面反光，赛博氛围。",
        },
    ]


def build_collection(client: QdrantClient, vector_size: int) -> None:
    """
    创建 Named Vectors collection。

    重点：
    - 同一个 point 里同时存 text_vector 和 image_vector
    - 两个向量字段可以独立指定参数
    """
    if client.collection_exists(collection_name=COLLECTION_NAME):
        client.delete_collection(collection_name=COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "text_vector": VectorParams(size=vector_size, distance=Distance.COSINE),
            "image_vector": VectorParams(size=vector_size, distance=Distance.COSINE),
        },
    )


def upsert_multimodal_points(client: QdrantClient, samples: list[dict]) -> None:
    """生成双模态向量并写入 Qdrant。"""
    text_inputs = [x["text_caption"] for x in samples]
    image_inputs = [x["image_caption"] for x in samples]

    text_vectors = embed_texts(text_inputs)
    image_vectors = embed_texts(image_inputs)

    points = []
    for sample, tvec, ivec in zip(samples, text_vectors, image_vectors):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "text_vector": tvec,
                    "image_vector": ivec,
                },
                payload={
                    "object_id": sample["object_id"],
                    "category": sample["category"],
                    "text_caption": sample["text_caption"],
                    "image_caption": sample["image_caption"],
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)


def search_text_to_image(client: QdrantClient, text_query: str, limit: int = 3) -> None:
    """
    文搜图：
    - 输入文本 query
    - 在 image_vector 空间检索
    """
    query_vec = embed_texts([text_query])[0]
    resp = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vec,
        using="image_vector",
        limit=limit,
        with_payload=True,
    )

    print("\n=== 文搜图（text -> image_vector）===")
    print(f"Query: {text_query}")
    for i, p in enumerate(resp.points, start=1):
        payload = p.payload or {}
        print(
            f"{i}. score={float(p.score):.4f} | object_id={payload.get('object_id')} "
            f"| category={payload.get('category')} | image_caption={payload.get('image_caption')}"
        )


def search_image_to_image(client: QdrantClient, sample: dict, limit: int = 3) -> None:
    """
    图搜图：
    - 这里用 sample 的 image_caption 近似“图像特征输入”
    - 在 image_vector 空间检索相似图
    """
    query_vec = embed_texts([sample["image_caption"]])[0]
    resp = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vec,
        using="image_vector",
        limit=limit,
        with_payload=True,
    )

    print("\n=== 图搜图（image-like query -> image_vector）===")
    print(f"Image-like query: {sample['image_caption']}")
    for i, p in enumerate(resp.points, start=1):
        payload = p.payload or {}
        print(
            f"{i}. score={float(p.score):.4f} | object_id={payload.get('object_id')} "
            f"| category={payload.get('category')} | image_caption={payload.get('image_caption')}"
        )


def search_image_to_text(client: QdrantClient, sample: dict, limit: int = 3) -> None:
    """
    图搜文：
    - 用“图像语义向量”去 text_vector 空间找最相关文本描述
    - 目的是演示跨模态路由（using=text_vector）
    """
    query_vec = embed_texts([sample["image_caption"]])[0]
    resp = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vec,
        using="text_vector",
        limit=limit,
        with_payload=True,
    )

    print("\n=== 图搜文（image-like query -> text_vector）===")
    print(f"Image-like query: {sample['image_caption']}")
    for i, p in enumerate(resp.points, start=1):
        payload = p.payload or {}
        print(
            f"{i}. score={float(p.score):.4f} | object_id={payload.get('object_id')} "
            f"| category={payload.get('category')} | text_caption={payload.get('text_caption')}"
        )


if __name__ == "__main__":
    if not QDRANT_API_KEY:
        raise ValueError("Please set QDRANT_API_KEY for remote Qdrant authentication.")

    # 1) 连接 Qdrant
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # 2) 构造样本并准备 collection
    samples = build_multimodal_samples()
    # 先用任意一句得到向量维度
    sample_vec_size = len(embed_texts([samples[0]["text_caption"]])[0])
    build_collection(client, vector_size=sample_vec_size)

    # 3) 写入双模态 points
    upsert_multimodal_points(client, samples)
    print(f"Collection ready: {COLLECTION_NAME}")
    print(f"Inserted points: {len(samples)}")
    print(f"Vector dim: {sample_vec_size}")

    # 4) 三类多模态检索演示
    search_text_to_image(client, text_query="我想找一张夜晚霓虹灯和雨后街道反光的图片", limit=3)
    search_image_to_image(client, sample=samples[2], limit=3)
    search_image_to_text(client, sample=samples[1], limit=3)
