"""
LangChain 详细学习示例 - 使用通义千问（Qwen）模型

前置准备:
1. 安装: pip install langchain-openai langchain-core
2. LangChain 中文文档: https://python.langchain.com.cn/
3. 官方文档: https://python.langchain.com/docs/introduction/

核心概念:
- ChatModel: 对话模型（替换底层 LLM，上层逻辑不变）
- Prompt Template: 提示词模板，管理 prompt 结构
- Chain: 链，将组件串联起来
- Memory: 记忆，管理对话历史
- Agent: 代理，让模型自主调用工具完成任务
- Document Loader: 文档加载器，读取各种格式文件
- Vector Store: 向量存储，语义搜索基础
- RAG: 检索增强生成，结合外部知识回答
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

# ============================================================
# 0. 初始化模型
# ============================================================
print("=" * 60)
print("0. 初始化模型 - ChatOpenAI")
print("=" * 60)

# LangChain 的 ChatOpenAI 兼容所有 OpenAI 格式接口，包括千问
llm = ChatOpenAI(
    model="qwen-plus",
    openai_api_key=os.getenv("DASHSCOPE_API_KEY", "sk-51b422ad7151406b8c3ddb1ce0a424ba"),
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7,
)

# 测试模型是否可用
test_resp = llm.invoke("你好")
print(f"模型: {test_resp.response_metadata.get('model_name', 'qwen-plus')}")
print(f"测试回答: {test_resp.content}")


# ============================================================
# 1. Message 类型 - 消息角色
# ============================================================
print("\n" + "=" * 60)
print("1. Message 类型 - 系统/用户/助手消息")
print("=" * 60)

messages = [
    SystemMessage(content="你是一个简洁的AI，回答控制在50字以内。"),
    HumanMessage(content="什么是机器学习？"),
]

response = llm.invoke(messages)
print(f"回答: {response.content}")

# 直接传递字符串（自动转为 HumanMessage）
response2 = llm.invoke("Python有什么特点？")
print(f"字符串直接传入: {response2.content}")


# ============================================================
# 2. Prompt Template - 提示词模板
# ============================================================
print("\n" + "=" * 60)
print("2. Prompt Template - 提示词模板")
print("=" * 60)

# 2.1 简单模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，用{tone}的语气回答问题。"),
    ("human", "请解释: {topic}"),
])

# 格式化查看 prompt
formatted = prompt.invoke({
    "role": "编程老师",
    "tone": "幽默",
    "topic": "什么是递归？",
})
print(f"格式化后的 prompt:")
print(formatted.to_string())

# 直接调用 LLM
response = llm.invoke(formatted)
print(f"回答: {response.content}")


# 2.2 模板 + 链式调用（LCEL 语法）
print("\n--- 2.2 LCEL 链式调用 ---")

# LCEL (LangChain Expression Language): 用 | 连接组件
chain = prompt | llm | StrOutputParser()

result = chain.invoke({
    "role": "数学老师",
    "tone": "严谨",
    "topic": "什么是微积分？",
})
print(f"LCEL 链式调用结果: {result}")


# 2.3 带聊天历史的模板
print("\n--- 2.3 带聊天历史占位符 ---")

history_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有用的助手。"),
    MessagesPlaceholder(variable_name="chat_history"),  # 历史消息占位符
    ("human", "{input}"),
])

chat_history = [
    HumanMessage(content="我喜欢吃苹果"),
    AIMessage(content="好的，我记住了你喜欢苹果。"),
]

formatted2 = history_prompt.invoke({
    "chat_history": chat_history,
    "input": "我喜欢吃什么？",
})
response = llm.invoke(formatted2)
print(f"带历史的回答: {response.content}")


# ============================================================
# 3. Output Parser - 输出解析器
# ============================================================
print("\n" + "=" * 60)
print("3. Output Parser - 输出解析器")
print("=" * 60)

# 3.1 字符串解析器（最常用）
parser = StrOutputParser()
chain = prompt | llm | parser
result = chain.invoke({"role": "科普作者", "tone": "通俗", "topic": "量子纠缠"})
print(f"StrOutputParser: {result[:150]}...\n")

# 3.2 JSON 解析器
from langchain_core.output_parsers import JsonOutputParser

json_prompt = ChatPromptTemplate.from_messages([
    ("system", "你只输出JSON，不要输出其他文字。"),
    ("human", "生成{count}个{name_type}的信息，格式: {{name, description}}"),
])

json_chain = json_prompt | llm | JsonOutputParser()
result = json_chain.invoke({"count": 3, "name_type": "编程语言"})
print(f"JsonOutputParser:")
import json
print(json.dumps(result, ensure_ascii=False, indent=2))


# ============================================================
# 4. 流式输出
# ============================================================
print("\n" + "=" * 60)
print("4. 流式输出")
print("=" * 60)

chain = prompt | llm | StrOutputParser()

print("流式输出: ", end="", flush=True)
for chunk in chain.stream({
    "role": "诗人",
    "tone": "优雅",
    "topic": "用现代诗描述大海",
}):
    print(chunk, end="", flush=True)
print()


# ============================================================
# 5. 异步调用
# ============================================================
print("\n" + "=" * 60)
print("5. 异步调用")
print("=" * 60)

import asyncio


async def parallel_chat():
    """同时发起多个请求"""
    topics = ["太阳为什么发光", "月亮为什么会变形状", "星星为什么闪烁"]

    chains = []
    for topic in topics:
        p = ChatPromptTemplate.from_messages([
            ("system", "你是一个科普专家，用简洁的语言回答。"),
            ("human", topic),
        ])
        chains.append(p | llm | StrOutputParser())

    # 并行执行（异步批量调用）
    results = await asyncio.gather(*[c.ainvoke({}) for c in chains])

    for topic, result in zip(topics, results):
        print(f"Q: {topic}")
        print(f"A: {result[:100]}...\n")


# 在普通脚本中运行异步代码
asyncio.run(parallel_chat())


# ============================================================
# 6. 工具（Tools）
# ============================================================
print("\n" + "=" * 60)
print("6. 工具（Tools）")
print("=" * 60)

from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """简单的数学计算器，接受数学表达式如 '2 + 3 * 4'"""
    try:
        # 安全的数学计算（仅允许数学运算）
        allowed = set("0123456789+-*/(). ")
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "表达式包含非法字符"
    except Exception as e:
        return f"计算错误: {e}"


@tool
def get_current_time() -> str:
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 查看工具信息
print("工具列表:")
for t in [calculator, get_current_time]:
    print(f"  - {t.name}: {t.description}")

# 手动调用工具
calc_result = calculator.invoke("123 * 456")
print(f"计算器结果: {calc_result}")
time_result = get_current_time.invoke({})
print(f"时间结果: {time_result}")


# ============================================================
# 7. Agent - 智能代理
# ============================================================
print("\n" + "=" * 60)
print("7. Agent - 智能代理（让模型自主选择工具）")
print("=" * 60)

from langgraph.prebuilt import create_react_agent

# 创建 ReAct Agent
tools = [calculator, get_current_time]
agent = create_react_agent(llm, tools)

# 运行 Agent
print("问题: 计算 234 * 567 等于多少？")
result = agent.invoke({
    "messages": [HumanMessage(content="计算 234 * 567 等于多少？")]
})
print(f"Agent 回答: {result['messages'][-1].content}")

print("\n问题: 现在几点了？")
result = agent.invoke({
    "messages": [HumanMessage(content="现在几点了？")]
})
print(f"Agent 回答: {result['messages'][-1].content}")


# ============================================================
# 8. Memory - 对话记忆
# ============================================================
print("\n" + "=" * 60)
print("8. Memory - 对话记忆")
print("=" * 60)

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langgraph.checkpoint.memory import MemorySaver

# 使用 MemorySaver 实现持久化记忆
agent_with_memory = create_react_agent(
    llm,
    tools,
    checkpointer=MemorySaver(),
)

config = {"configurable": {"thread_id": "user_001"}}

# 第一轮
print("User: 我叫张三，今年25岁")
result = agent_with_memory.invoke(
    {"messages": [HumanMessage(content="我叫张三，今年25岁")]},
    config=config,
)
print(f"AI: {result['messages'][-1].content}")

# 第二轮 - 模型应该能记住之前的信息
print("\nUser: 我叫什么名字？")
result = agent_with_memory.invoke(
    {"messages": [HumanMessage(content="我叫什么名字？")]},
    config=config,
)
print(f"AI: {result['messages'][-1].content}")


# ============================================================
# 9. Document Loader - 文档加载
# ============================================================
print("\n" + "=" * 60)
print("9. Document Loader - 文档加载")
print("=" * 60)

from langchain_core.documents import Document

# 手动创建文档（实际使用中可从文件加载）
docs = [
    Document(
        page_content="Python是一种广泛使用的高级编程语言，由Guido van Rossum于1991年首次发布。",
        metadata={"source": "python_intro", "type": "text"},
    ),
    Document(
        page_content="Python支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。",
        metadata={"source": "python_features", "type": "text"},
    ),
    Document(
        page_content="Python的设计理念强调代码可读性，其语法结构清晰简洁，适合初学者学习。",
        metadata={"source": "python_design", "type": "text"},
    ),
]

for doc in docs:
    print(f"来源: {doc.metadata['source']}")
    print(f"内容: {doc.page_content[:50]}...\n")

# 常用 Document Loader（需要额外安装包）:
# - TextLoader: 纯文本文件 (langchain-community)
# - PyPDFLoader: PDF 文件 (pypdf)
# - Docx2txtLoader: Word 文档 (docx2txt)
# - CSVLoader: CSV 文件
# - WebBaseLoader: 网页内容 (beautifulsoup4)
# - DirectoryLoader: 加载整个目录


# ============================================================
# 10. Vector Store - 向量存储与语义搜索
# ============================================================
print("\n" + "=" * 60)
print("10. Vector Store - 向量存储与语义搜索")
print("=" * 60)

# 使用 FAISS 作为向量数据库
# 安装: pip install faiss-cpu langchain-community langchain-huggingface

try:
    from langchain_community.vectorstores import FAISS
    from langchain_core.embeddings import Embeddings

    # 简化的 Embedding 类（使用千问）
    class DashScopeEmbeddings(Embeddings):
        """使用千问模型生成向量"""
        def __init__(self, model="text-embedding-v3"):
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("DASHSCOPE_API_KEY", "sk-51b422ad7151406b8c3ddb1ce0a424ba"),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            self.model = model

        def embed_documents(self, texts):
            resp = self.client.embeddings.create(
                model=self.model, input=texts
            )
            return [e.embedding for e in resp.data]

        def embed_query(self, text):
            return self.embed_documents([text])[0]

    # 创建向量存储
    embeddings = DashScopeEmbeddings()
    vector_store = FAISS.from_documents(docs, embeddings)

    # 语义搜索
    print("搜索: 'Python的设计特点'")
    results = vector_store.similarity_search("Python的设计特点", k=2)
    for i, doc in enumerate(results):
        print(f"  [{i+1}] {doc.page_content}")
        print(f"      来源: {doc.metadata}")

except ImportError:
    print("（跳过向量存储示例，安装依赖后可运行:）")
    print("  pip install faiss-cpu langchain-community")


# ============================================================
# 11. RAG - 检索增强生成
# ============================================================
print("\n" + "=" * 60)
print("11. RAG - 检索增强生成")
print("=" * 60)

# RAG 完整流程
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个知识问答助手。请根据以下参考资料回答用户的问题。
如果参考资料中没有相关信息，请直接告诉用户你不知道。

参考资料:
{context}"""),
    ("human", "{question}"),
])

try:
    # 如果向量存储可用，演示完整 RAG 流程
    from langchain_community.vectorstores import FAISS

    vector_store = FAISS.from_documents(docs, embeddings)

    def rag_query(question):
        # 1. 检索相关文档
        retrieved = vector_store.similarity_search(question, k=2)
        context = "\n\n".join(d.page_content for d in retrieved)

        # 2. 生成回答
        chain = rag_prompt | llm | StrOutputParser()
        return chain.invoke({"context": context, "question": question})

    print("问题: Python适合初学者学习吗？为什么？")
    answer = rag_query("Python适合初学者学习吗？为什么？")
    print(f"回答: {answer}")

except (ImportError, NameError):
    # 不依赖外部库的简化 RAG 演示
    print("（演示简化版 RAG，无需向量库）")

    # 简单的关键词匹配检索
    def simple_retrieve(question, k=2):
        """基于关键词的简单检索"""
        words = set(question.lower())
        scored = []
        for doc in docs:
            score = sum(1 for w in words if w in doc.page_content.lower())
            scored.append((score, doc))
        scored.sort(reverse=True)
        return [doc for _, doc in scored[:k]]

    def simple_rag(question):
        context = "\n\n".join(d.page_content for d in simple_retrieve(question))
        chain = rag_prompt | llm | StrOutputParser()
        return chain.invoke({"context": context, "question": question})

    print("问题: Python有什么特点？")
    answer = simple_rag("Python有什么特点？")
    print(f"回答: {answer}")


# ============================================================
# 12. 批量处理 - 一次处理多个输入
# ============================================================
print("\n" + "=" * 60)
print("12. 批量处理")
print("=" * 60)

chain = prompt | llm | StrOutputParser()

inputs = [
    {"role": "历史学家", "tone": "专业", "topic": "秦始皇统一六国"},
    {"role": "物理学家", "tone": "通俗", "topic": "相对论"},
    {"role": "生物学家", "tone": "生动", "topic": "DNA双螺旋结构"},
]

print("批量生成3个主题的内容:\n")
for result in chain.batch(inputs):
    print(f"--- {result[:80]}... ---\n")


# ============================================================
# 13. 回调（Callbacks）- 追踪执行过程
# ============================================================
print("\n" + "=" * 60)
print("13. 回调 - 追踪执行过程")
print("=" * 60)

from langchain_core.callbacks import BaseCallbackHandler


class SimpleCallback(BaseCallbackHandler):
    """简单回调，打印执行信息"""
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"  [LLM开始] 接收到 {len(prompts)} 个 prompt")

    def on_llm_end(self, response, **kwargs):
        tokens = response.llm_output.get('token_usage', {}) if response.llm_output else {}
        print(f"  [LLM结束] 生成完成")

    def on_chain_start(self, serialized, inputs, **kwargs):
        print(f"  [Chain开始] 执行链")

    def on_chain_end(self, outputs, **kwargs):
        print(f"  [Chain结束] 输出 {len(str(outputs))} 字符")


chain = prompt | llm | StrOutputParser()
result = chain.invoke(
    {"role": "科普作家", "tone": "幽默", "topic": "为什么天空是蓝色的？"},
    config={"callbacks": [SimpleCallback()]},
)
print(f"回答: {result[:100]}...")


# ============================================================
# 14. 总结: LangChain 核心组件关系图
# ============================================================
print("\n" + "=" * 60)
print("14. LangChain 核心组件关系")
print("=" * 60)

summary = """
LangChain 核心架构:

┌─────────────────────────────────────────────────────┐
│                    Application                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐   │
│  │  Prompt   │───▶│   LLM    │───▶│   Output     │   │
│  │ Template  │    │ (ChatModel)│   │   Parser     │   │
│  └──────────┘    └──────────┘    └──────────────┘   │
│       │               │                              │
│       ▼               ▼                              │
│  ┌──────────┐    ┌──────────┐                        │
│  │  Memory   │    │  Tools   │                        │
│  │(History)  │    │(Actions) │                        │
│  └──────────┘    └──────────┘                        │
│                                                      │
│  ┌──────────────────────────────────────┐            │
│  │           Agent                       │            │
│  │  (Prompt + LLM + Tools + Memory)      │            │
│  └──────────────────────────────────────┘            │
│                                                      │
│  ┌──────────────────────────────────────┐            │
│  │           RAG Pipeline                │            │
│  │  (Loader → Split → Embed → Store     │            │
│  │   → Retrieve → Generate)             │            │
│  └──────────────────────────────────────┘            │
└─────────────────────────────────────────────────────┘

LCEL (LangChain Expression Language):
  chain = prompt | llm | parser

  支持: .invoke() / .stream() / .batch() / .ainvoke()
"""
print(summary)
