import os
import time
import uuid
from statistics import mean

import dashscope
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, HnswConfigDiff, PointStruct, SearchParams, VectorParams


# 远程 Qdrant 地址（你当前使用的是 HTTP）
QDRANT_URL = os.getenv("QDRANT_URL", "http://115.190.125.94/")
# Qdrant 鉴权 Key（如果实例开启鉴权则必须提供）
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "root")
# 千问 embedding 模型名称
QWEN_EMBEDDING_MODEL = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")
# 实验集合名前缀，每组参数都会创建一个独立 collection
COLLECTION_PREFIX = os.getenv("QDRANT_COLLECTION_PREFIX", "qdrant_idx_tuning")


def embed_texts(texts: list[str], batch_size: int = 10) -> list[list[float]]:
    """调用千问 embedding，按批次生成向量。"""
    # DashScope API Key 从环境变量读取，避免硬编码在脚本里。
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("Please set DASHSCOPE_API_KEY")

    dashscope.api_key = api_key

    vectors: list[list[float]] = []
    # 千问 embedding 接口单次请求有数量上限，分批最稳妥。
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = dashscope.TextEmbedding.call(model=QWEN_EMBEDDING_MODEL, input=batch)
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding failed: {resp}")

        # 返回向量顺序与输入 batch 顺序一致，可直接拼接。
        vectors.extend([item["embedding"] for item in resp.output["embeddings"]])

    return vectors


def build_dataset() -> tuple[list[str], list[str], dict[str, str]]:
    """构造中文文档、中文查询与 ground truth。"""
    docs = [
        "Qdrant 通过向量和元数据 payload 实现语义检索。",
        "HNSW 参数会影响召回率与查询延迟的平衡。",
        "元数据过滤可以提升向量检索的业务准确性。",
        "混合检索会结合稠密向量和稀疏特征。",
        "多模态检索支持文本到图像的跨模态搜索。",
        "向量维度必须和 collection 配置完全一致。",
        "提高 hnsw_ef 通常会增加召回率但也会增加延迟。",
        "ef_construct 决定索引构建质量和构建时间。",
        "文本语义检索里常用余弦距离计算相似度。",
        "TopK 设置会影响噪声比例和召回覆盖率。",
    ]

    queries = [
        "Qdrant 如何存储语义向量？",
        "哪些参数会影响 HNSW 的召回？",
        "为什么向量检索需要元数据过滤？",
        "混合检索的核心思路是什么？",
    ]

    # ground_truth：每个 query 期望命中的标准答案文档。
    # 这里为了学习调参，采用“单 query 对应单标准文档”的简化标注。
    ground_truth = {
        queries[0]: docs[0],
        queries[1]: docs[1],
        queries[2]: docs[2],
        queries[3]: docs[3],
    }
    return docs, queries, ground_truth


def recall_at_k(results: list[list[str]], expected: list[str], k: int) -> float:
    """计算 Recall@K。"""
    # Recall@K：期望答案是否出现在前 K 条结果中。
    # 例如 4 个查询里命中 3 个，则 Recall@K = 0.75。
    hit = 0
    for top_texts, exp in zip(results, expected):
        if exp in top_texts[:k]:
            hit += 1
    return hit / len(expected)


def percentile_95(values: list[float]) -> float:
    """计算 P95 延迟。"""
    if not values:
        return 0.0
    arr = sorted(values)
    idx = int(0.95 * (len(arr) - 1))
    return arr[idx]


if __name__ == "__main__":
    if not QDRANT_API_KEY:
        raise ValueError("Please set QDRANT_API_KEY for remote Qdrant authentication.")

    # 1) 准备固定数据集（调参时必须固定数据，保证结果可比较）
    docs, queries, gt = build_dataset()

    # 2) 生成文档向量与查询向量
    doc_vectors = embed_texts(docs)
    query_vectors = embed_texts(queries)

    # 向量维度由模型决定；创建 collection 时必须一致，否则写入会报错。
    vector_size = len(doc_vectors[0])

    # 3) 定义待实验的参数组合
    # m、ef_construct 影响“建索引质量/资源”，hnsw_ef 影响“查询召回/延迟”。
    param_sets = [
        {"m": 16, "ef_construct": 100, "hnsw_ef": 64},
        {"m": 16, "ef_construct": 200, "hnsw_ef": 64},
        {"m": 24, "ef_construct": 200, "hnsw_ef": 64},
        {"m": 24, "ef_construct": 200, "hnsw_ef": 128},
    ]

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    print("=== Qdrant 索引参数调优实验 ===")
    print(f"Qdrant URL: {QDRANT_URL}")
    print(f"Embedding 模型: {QWEN_EMBEDDING_MODEL}")
    print(f"向量维度: {vector_size}")

    for i, params in enumerate(param_sets, start=1):
        # 每组参数使用独立 collection，避免历史数据污染。
        collection_name = f"{COLLECTION_PREFIX}_{i}"

        # 为了保证可重复实验：存在则删除，再按当前参数重新创建。
        if client.collection_exists(collection_name=collection_name):
            client.delete_collection(collection_name=collection_name)

        client.create_collection(
            collection_name=collection_name,
            # 文本检索通常使用余弦距离
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            # HNSW 建索引参数
            hnsw_config=HnswConfigDiff(m=params["m"], ef_construct=params["ef_construct"]),
        )

        # 4) 写入相同训练文档，确保参数之间公平对比。
        points = []
        for text, vector in zip(docs, doc_vectors):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={"text": text},
                )
            )
        client.upsert(collection_name=collection_name, points=points)

        # 5) 在同一查询集上统计召回和延迟
        top_texts_per_query: list[list[str]] = []
        query_latencies: list[float] = []

        for qvec in query_vectors:
            t0 = time.perf_counter()

            # 兼容你当前 qdrant-client：使用 query_points（非 search）
            response = client.query_points(
                collection_name=collection_name,
                query=qvec,
                # 查询阶段 HNSW 参数
                search_params=SearchParams(hnsw_ef=params["hnsw_ef"]),
                limit=3,
                with_payload=True,
            )

            elapsed_ms = (time.perf_counter() - t0) * 1000
            query_latencies.append(elapsed_ms)

            hits = response.points if hasattr(response, "points") else []
            top_texts_per_query.append([hit.payload.get("text", "") for hit in hits if hit.payload])

        # 6) 计算本组参数的 Recall@3
        expected = [gt[q] for q in queries]
        r3 = recall_at_k(top_texts_per_query, expected, k=3)

        # AvgLatency 看平均性能，P95 观察长尾延迟。
        print(
            f"params(m={params['m']}, ef_construct={params['ef_construct']}, hnsw_ef={params['hnsw_ef']}) "
            f"=> Recall@3={r3:.2f}, AvgLatency={mean(query_latencies):.2f}ms, P95={percentile_95(query_latencies):.2f}ms"
        )
