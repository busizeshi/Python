import os
import re
import uuid
from collections import Counter

import dashscope
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


# -----------------------------
# 全局配置
# -----------------------------
# 远程 Qdrant 地址：默认使用你给的服务器地址。
QDRANT_URL = os.getenv("QDRANT_URL", "http://115.190.125.94/")
# Qdrant 鉴权 Key：如果服务开启鉴权，这个值必须正确。
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "root")
# 千问 embedding 模型：默认 text-embedding-v3。
QWEN_EMBEDDING_MODEL = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")
# 本模块 demo 使用的 collection 名称。
COLLECTION_NAME = os.getenv("QDRANT_HYBRID_COLLECTION", "qdrant_hybrid_demo")


def embed_texts(texts: list[str], batch_size: int = 10) -> list[list[float]]:
    """调用千问 embedding，按批次生成向量。"""
    # 说明：千问 embedding 接口需要 DASHSCOPE_API_KEY。
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("Please set DASHSCOPE_API_KEY")

    dashscope.api_key = api_key
    vectors: list[list[float]] = []

    # 关键点：按批请求，避免单次 input 过长或条数过多导致接口报错。
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = dashscope.TextEmbedding.call(model=QWEN_EMBEDDING_MODEL, input=batch)
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding failed: {resp}")

        # 将每个批次的 embedding 顺序追加到总列表。
        vectors.extend([item["embedding"] for item in resp.output["embeddings"]])

    return vectors


def tokenize_zh(text: str) -> list[str]:
    """简化中文分词：中文按连续片段切分，英文数字按单词切分。"""
    # 这里不用外部分词库，目的是让 demo 零额外依赖。
    # 正则逻辑：
    # 1) [\u4e00-\u9fff]+ 取连续中文段
    # 2) [a-zA-Z0-9_]+ 取英文/数字/下划线词
    tokens = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9_]+", text.lower())
    return [t for t in tokens if t.strip()]


def sparse_score(query: str, doc: str) -> float:
    """简化 sparse 打分：关键词重叠的 F1 风格分数。"""
    q_tokens = tokenize_zh(query)
    d_tokens = tokenize_zh(doc)
    if not q_tokens or not d_tokens:
        return 0.0

    # Counter 交集可以快速得到 token 重叠次数。
    q_counter = Counter(q_tokens)
    d_counter = Counter(d_tokens)
    overlap = sum((q_counter & d_counter).values())

    if overlap == 0:
        return 0.0

    # 这里用 F1 风格分数，让“精准匹配”和“覆盖查询”都被考虑。
    precision = overlap / max(len(d_tokens), 1)
    recall = overlap / max(len(q_tokens), 1)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def normalize_dense_score(score: float) -> float:
    """把余弦相似度分数压到 0~1，便于与 sparse 分数融合。"""
    # qdrant 余弦分数常在 [-1, 1]，线性映射到 [0, 1]。
    return max(0.0, min(1.0, (score + 1.0) / 2.0))


def build_docs() -> list[dict]:
    """构造中文样本文档。"""
    texts = [
        "Qdrant 支持向量存储与元数据过滤，适合语义检索系统。",
        "混合检索会并行使用稠密向量召回和关键词召回。",
        "HNSW 参数 m、ef_construct、hnsw_ef 会影响召回与延迟。",
        "多模态检索可以实现文本搜图和图搜图。",
        "向量维度必须与 collection 配置一致，否则写入会失败。",
        "关键词检索在产品型号、编号、专有词查询中更稳定。",
        "语义检索在同义改写和自然语言问答中更有优势。",
        "检索评测应同时关注 Recall、MRR 和 P95 延迟。",
    ]

    # 每个文档分配一个 UUID 作为点 ID。
    docs = []
    for i, t in enumerate(texts, start=1):
        docs.append({"id": str(uuid.uuid4()), "doc_id": i, "text": t})
    return docs


def build_index(client: QdrantClient, docs: list[dict]) -> None:
    """创建 collection 并写入文档向量。"""
    # 1) 文档转向量
    vectors = embed_texts([d["text"] for d in docs])
    dim = len(vectors[0])

    # 2) 清理旧 collection，保证重复运行时结果可复现
    if client.collection_exists(collection_name=COLLECTION_NAME):
        client.delete_collection(collection_name=COLLECTION_NAME)

    # 3) 新建 collection（Dense-only 场景，这里只建一个向量字段）
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    # 4) 组装点数据并写入
    points = []
    for d, v in zip(docs, vectors):
        points.append(
            PointStruct(
                id=d["id"],
                vector=v,
                payload={"doc_id": d["doc_id"], "text": d["text"]},
            )
        )
    client.upsert(collection_name=COLLECTION_NAME, points=points)


def dense_retrieve(client: QdrantClient, query: str, limit: int = 5) -> list[dict]:
    """Dense-only：向量检索。"""
    # 1) Query 先向量化
    qvec = embed_texts([query])[0]

    # 2) 用向量在 Qdrant 检索 TopK
    resp = client.query_points(
        collection_name=COLLECTION_NAME,
        query=qvec,
        limit=limit,
        with_payload=True,
    )

    # 3) 提取统一结果结构
    results = []
    for p in resp.points:
        results.append(
            {
                "id": str(p.id),
                "text": p.payload.get("text", "") if p.payload else "",
                # Dense 分数先归一化，后续可和 sparse 分数直接融合
                "dense_score": normalize_dense_score(float(p.score)),
            }
        )
    return results


def sparse_retrieve(docs: list[dict], query: str, limit: int = 5) -> list[dict]:
    """Sparse-only：本地关键词匹配打分。"""
    scored = []
    for d in docs:
        s = sparse_score(query, d["text"])
        if s > 0:
            scored.append({"id": d["id"], "text": d["text"], "sparse_score": s})

    # 分数降序排序，取前 limit 条
    scored.sort(key=lambda x: x["sparse_score"], reverse=True)
    return scored[:limit]


def hybrid_fuse(
    dense_hits: list[dict], sparse_hits: list[dict], w_dense: float = 0.7, w_sparse: float = 0.3
) -> list[dict]:
    """融合打分：hybrid = w_dense*dense + w_sparse*sparse。"""
    # 用 dict 做按文档 ID 的合并，避免重复文档出现多次。
    merged: dict[str, dict] = {}

    # 先写入 dense 结果
    for item in dense_hits:
        merged[item["id"]] = {
            "id": item["id"],
            "text": item["text"],
            "dense_score": item.get("dense_score", 0.0),
            "sparse_score": 0.0,
        }

    # 再并入 sparse 结果
    for item in sparse_hits:
        if item["id"] not in merged:
            merged[item["id"]] = {
                "id": item["id"],
                "text": item["text"],
                "dense_score": 0.0,
                "sparse_score": item.get("sparse_score", 0.0),
            }
        else:
            merged[item["id"]]["sparse_score"] = item.get("sparse_score", 0.0)

    # 计算融合分并排序
    fused = []
    for _, v in merged.items():
        hybrid_score = w_dense * v["dense_score"] + w_sparse * v["sparse_score"]
        fused.append(
            {
                "id": v["id"],
                "text": v["text"],
                "dense_score": v["dense_score"],
                "sparse_score": v["sparse_score"],
                "hybrid_score": hybrid_score,
            }
        )

    fused.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return fused


def print_hits(title: str, hits: list[dict], key: str) -> None:
    """打印单路检索结果（Dense-only 或 Sparse-only）。"""
    print(f"\n=== {title} ===")
    for i, h in enumerate(hits, start=1):
        print(f"{i}. {key}={h.get(key, 0.0):.4f} | text={h['text']}")


def print_hybrid(hits: list[dict], limit: int = 5) -> None:
    """打印融合后的结果，并展示分项分数用于解释排序。"""
    print("\n=== Hybrid 融合结果 ===")
    for i, h in enumerate(hits[:limit], start=1):
        print(
            f"{i}. hybrid={h['hybrid_score']:.4f} | dense={h['dense_score']:.4f} "
            f"| sparse={h['sparse_score']:.4f} | text={h['text']}"
        )


if __name__ == "__main__":
    # 远程服务鉴权检查
    if not QDRANT_API_KEY:
        raise ValueError("Please set QDRANT_API_KEY for remote Qdrant authentication.")

    # 1) 连接 Qdrant
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # 2) 准备样本并建索引
    docs = build_docs()
    build_index(client, docs)

    # 3) 准备查询（语义 + 关键词混合倾向）
    query = "如何让向量检索同时兼顾语义理解和关键词精确命中？"

    # 4) 三路检索
    dense_hits = dense_retrieve(client, query, limit=5)
    sparse_hits = sparse_retrieve(docs, query, limit=5)
    hybrid_hits = hybrid_fuse(dense_hits, sparse_hits, w_dense=0.7, w_sparse=0.3)

    # 5) 输出对比
    print(f"Query: {query}")
    print_hits("Dense-only", dense_hits, "dense_score")
    print_hits("Sparse-only", sparse_hits, "sparse_score")
    print_hybrid(hybrid_hits, limit=5)
