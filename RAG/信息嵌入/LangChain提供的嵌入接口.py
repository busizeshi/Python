import os

from langchain_openai import OpenAIEmbeddings


def build_qwen_embeddings() -> OpenAIEmbeddings:
    """
    通过千问（Qwen）兼容 OpenAI 的接口，构建 LangChain Embeddings 实例。
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请先设置 DASHSCOPE_API_KEY 环境变量。")

    model = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")
    base_url = os.getenv(
        "QWEN_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    return OpenAIEmbeddings(
        model=model,
        api_key=api_key,
        base_url=base_url,
        # DashScope 兼容端点期望 input 为字符串（或字符串列表），
        # 关闭 LangChain 的 token 分片路径，避免传入 token id 列表。
        check_embedding_ctx_length=False,
        tiktoken_enabled=False,
    )


if __name__ == "__main__":
    embeddings = build_qwen_embeddings()
    vector = embeddings.embed_query("LangChain 通过千问生成向量")
    print(f"向量维度: {len(vector)}")
