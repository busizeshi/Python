import os

from llama_index.embeddings.dashscope import DashScopeEmbedding


def build_qwen_embeddings() -> DashScopeEmbedding:
    """
    通过千问（Qwen）的 DashScope 接口，构建 LlamaIndex Embedding 实例。
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请先设置 DASHSCOPE_API_KEY 环境变量。")

    model_name = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")

    return DashScopeEmbedding(
        model_name=model_name,
        api_key=api_key,
    )


if __name__ == "__main__":
    embeddings = build_qwen_embeddings()
    vector = embeddings.get_text_embedding("LlamaIndex 通过千问生成向量")
    print(f"向量维度: {len(vector)}")

