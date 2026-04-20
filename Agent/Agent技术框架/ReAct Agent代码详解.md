# ReAct Agent 代码详解

## 一、整体架构

```
┌──────────────────────────────────────────────────┐
│                  AgentExecutor                    │
│                                                  │
│  用户输入 ──→ ReAct Prompt ──→ Qwen LLM ──→ 解析  │
│                                  ↑          │    │
│                                  │          ↓    │
│                            scratchpad   Action?  │
│                            追加结果      │    │
│                                  ↑      是↓  否  │
│                           SerpAPI搜索  Final Answer│
│                              (工具)    → 输出结果  │
└──────────────────────────────────────────────────┘
```

核心思想：**ReAct = Reasoning（推理）+ Acting（行动）**，LLM 先思考该做什么，再执行动作获取信息，循环往复直到能给出最终答案。

---

## 二、逐段代码解析

### 1. 环境变量配置

```python
import os

os.environ["DASHSCOPE_API_KEY"] = "sk-51b422ad7151406b8c3ddb1ce0a424ba"  # Qwen模型的API密钥
os.environ["SERPAPI_API_KEY"] = "97db7da7af0aa8b813d9ecca8595b1b9c4ed253b2d9bcaa15ec53a0f3568a6ea"
```

- **`DASHSCOPE_API_KEY`**：阿里云 DashScope 平台的 API 密钥，用于调用千问（Qwen）大模型
- **`SERPAPI_API_KEY`**：SerpAPI 的密钥，用于调用 Google 搜索 API 实现联网搜索

这两个密钥通过 `os.environ` 写入环境变量，后续各组件会自动读取。

---

### 2. 获取 ReAct 提示模板

```python
from langsmith import Client as LangSmithClient

ls_client = LangSmithClient()
prompt = ls_client.pull_prompt("hwchase17/react")
print("ReAct Prompt:")
print(prompt)
```

- 从 **LangSmith Hub**（原 LangChain Hub）拉取标准的 ReAct 提示模板
- `hwchase17/react` 是社区中最经典的 ReAct prompt 模板
- 该模板定义了 Agent 的思考-行动循环格式

模板核心结构如下：

```
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
```

模板中有 4 个占位变量：

| 变量 | 作用 |
|------|------|
| `{tools}` | 注入所有可用工具的名称和描述 |
| `{tool_names}` | 注入工具名称列表，约束 Agent 只能选择这些工具 |
| `{input}` | 用户的原始问题 |
| `{agent_scratchpad}` | Agent 的思维过程记录（之前的 Thought/Action/Observation） |

---

### 3. 加载千问大模型

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="qwen-max",
    openai_api_key=os.environ["DASHSCOPE_API_KEY"],
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
```

- 使用 `ChatOpenAI` 类，而不是 `Tongyi` 类——因为阿里云提供了 **OpenAI 兼容接口**
- **`model="qwen-max"`**：选择千问最强版本模型
- **`openai_api_base`**：指向 DashScope 的 OpenAI 兼容端点，这样 LangChain 的 OpenAI 适配器可以直接调用千问模型，无需额外适配

> 本质上是"借壳"——用 OpenAI 的协议格式去调用千问的模型服务。

---

### 4. 配置联网搜索工具

```python
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import Tool

search = SerpAPIWrapper()

tools = [
    Tool(
        name="Search",
        func=search.run,
        description="当大模型没有相关知识时，用于搜索知识"
    ),
]
```

- **`SerpAPIWrapper`**：封装了 SerpAPI（Google 搜索 API），调用 `search.run("查询内容")` 即可返回搜索结果
- **`Tool`**：LangChain 的工具定义类，将任意函数包装成 Agent 可调用的工具，包含三个关键字段：
  - `name`：工具名称，Agent 在 `Action` 字段中写这个名字来调用
  - `func`：实际执行的函数
  - `description`：工具描述，**LLM 根据这个描述决定何时使用该工具**（非常重要！）

> `tools` 列表可以包含多个工具，这里只配置了搜索一个。

---

### 5. 构建 ReAct Agent

```python
from langchain_classic.agents import create_react_agent, AgentExecutor

agent = create_react_agent(llm, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

#### create_react_agent 参数说明

| 参数 | 作用 |
|------|------|
| `llm` | 大语言模型，负责推理 |
| `tools` | 可用工具列表 |
| `prompt` | ReAct 提示模板 |

返回的 `agent` 是一个 `RunnableSequence`（可执行链），它将 prompt → llm → 输出解析器串联起来。

#### AgentExecutor 的作用

`AgentExecutor` 是整个循环的调度中心，负责：

1. 将用户输入填充到 prompt 模板
2. 调用 LLM 生成回复
3. 解析 LLM 输出中的 `Action` 和 `Action Input`
4. 调用对应工具执行动作
5. 将 `Observation` 追加到 `agent_scratchpad`
6. 重复上述过程，直到 LLM 输出 `Final Answer`
7. `verbose=True` 打印每一步的详细过程

> 为什么用 `langchain_classic`？因为 LangChain 1.2+ 版本将 ReAct 相关类迁移到了 `langchain_classic.agents` 模块，原 `langchain.agents` 中的已弃用。

---

### 6. 执行查询

```python
result = agent_executor.invoke({"input": "当前Agent最新研究进展是什么？"})
print("\n最终结果:")
print(result["output"])
```

- `invoke` 接收一个字典，`input` 键对应的是用户问题
- `result` 是一个字典，`result["output"]` 就是最终的 `Final Answer`

---

## 三、完整执行流程示例

以问题 "当前Agent最新研究进展是什么？" 为例：

```
用户问题 → 填充prompt → LLM推理
  ↓
Thought: 我需要搜索Agent的最新研究进展
Action: Search
Action Input: "Agent最新研究进展"
  ↓
调用 SerpAPI 执行搜索 → 返回结果
  ↓
Observation: [搜索结果内容...]
  ↓
将 Observation 追加到 scratchpad → 再次调用 LLM
  ↓
Thought: 我现在知道最终答案了
Final Answer: [综合搜索结果生成的回答]
```

---

## 四、依赖安装

运行前需确保已安装以下依赖：

```bash
pip install langchain langchain-classic langchain-openai langchain-community langsmith dashscope google-search-results
```

| 包名 | 作用 |
|------|------|
| `langchain` | LangChain 核心框架 |
| `langchain-classic` | 兼容旧版 ReAct Agent API（create_react_agent, AgentExecutor） |
| `langchain-openai` | OpenAI 兼容接口适配器 |
| `langchain-community` | 社区工具集成（SerpAPIWrapper 等） |
| `langsmith` | LangSmith SDK，用于拉取 Hub 上的 prompt 模板 |
| `dashscope` | 阿里云 DashScope SDK |
| `google-search-results` | SerpAPI 的 Python 客户端 |

---

## 五、关键兼容性说明

| 问题 | 解决方案 |
|------|----------|
| `Tool` 导入路径变更 | 从 `langchain_core.tools` 导入，非旧版 `langchain.agents.tools` |
| `create_react_agent` 迁移 | 从 `langchain_classic.agents` 导入，非 `langchain.agents` |
| `AgentExecutor` 迁移 | 从 `langchain_classic.agents` 导入，非 `langchain.agents` |
| LangChain Hub 拉取方式 | 使用 `langsmith.Client.pull_prompt()`，非旧版 `langchainhub` |
| Qwen 模型调用方式 | 使用 `ChatOpenAI` + DashScope 兼容端点，非 `Tongyi` 类 |
