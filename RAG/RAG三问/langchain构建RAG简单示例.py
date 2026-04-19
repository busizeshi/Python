import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

# 设置 DashScope API Key
# 获取地址：https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key
os.environ["DASHSCOPE_API_KEY"] = "sk-51b422ad7151406b8c3ddb1ce0a424ba"

# 1. 加载文档
loader = DirectoryLoader(
    "../data/黑悟空", 
    glob="**/*.txt",
    loader_cls=TextLoader,  # 使用轻量级 TextLoader，避免安装 unstructured
    loader_kwargs={"encoding": "utf-8"}
)
documents = loader.load()
print(f"加载了 {len(documents)} 个文档")

# 2. 文本分割
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # 每个文本块的大小
    chunk_overlap=50  # 文本块之间的重叠
)
texts = text_splitter.split_documents(documents)
print(f"分割成 {len(texts)} 个文本块")

# 3. 创建 Embedding（使用本地 HuggingFace 模型，免费且无需 API Key）
embeddings = HuggingFaceEmbeddings(
    model_name="shibing624/text2vec-base-chinese"
)

# 4. 创建向量数据库
vectorstore = FAISS.from_documents(texts, embeddings)

# 5. 创建检索器
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})  # 返回最相关的 3 个文档

# 6. 配置千问大语言模型
llm = ChatOpenAI(
    model="qwen-turbo",  # 或 qwen-plus, qwen-max
    openai_api_key=os.environ["DASHSCOPE_API_KEY"],
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7
)

# 7. 构建 RAG 提示词模板
template = """
你是一个知识助手。请根据以下提供的上下文信息来回答问题。
如果无法从上下文中找到答案，请说明你不知道。

上下文：
{context}

问题：{question}

请回答：
"""

prompt = ChatPromptTemplate.from_template(template)

# 8. 构建 RAG 链
def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 9. 执行查询
question = "《黑神话：悟空》中有那些故事章节"
print(f"\n问题：{question}\n")
response = rag_chain.invoke(question)
print(f"回答：{response}")
