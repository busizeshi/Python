import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.llms.dashscope import DashScope

# 设置 DashScope API Key（请替换为你的真实 API Key）
# 获取地址：https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key
os.environ["DASHSCOPE_API_KEY"] = "sk-51b422ad7151406b8c3ddb1ce0a424ba"

# 读取文档
print("📄 步骤 1/4: 正在读取文档...")
documents = SimpleDirectoryReader("../data/黑悟空").load_data()
print(f"✅ 成功加载 {len(documents)} 个文档")

# 配置千问 embedding 模型
print("⚙️  正在配置 Embedding 模型...")
Settings.embed_model = DashScopeEmbedding(
    model_name="text-embedding-v3",  # 或使用 text-embedding-v2
    api_key=os.environ["DASHSCOPE_API_KEY"],
    embed_batch_size=10  # DashScope 限制单次 batch 最多 10 条
)
print("✅ Embedding 模型配置完成")

# 配置千问 LLM 模型
print("⚙️  正在配置 LLM 模型...")
Settings.llm = DashScope(
    model="qwen-turbo",  # 或 qwen-plus, qwen-max
    api_key=os.environ["DASHSCOPE_API_KEY"]
)
print("✅ LLM 模型配置完成")

# 构建索引
print("\n🔧 步骤 2/4: 正在构建向量索引...")
print("💡 提示: 这需要调用 DashScope API 向量化所有文档，请耐心等待...")
import time
start_time = time.time()
index = VectorStoreIndex.from_documents(documents)
elapsed = time.time() - start_time
print(f"✅ 索引构建完成（耗时: {elapsed:.2f} 秒）")

# 创建查询引擎
print("\n🔍 步骤 3/4: 正在创建查询引擎...")
query_engine = index.as_query_engine()
print("✅ 查询引擎创建完成")

# 查询
question = "《黑神话： 悟空》 中有哪些战斗工具？"
print(f"\n💬 步骤 4/4: 正在查询: {question}")
response = query_engine.query(question)
print("\n" + "="*50)
print(f"回答: {response}")
print("="*50)