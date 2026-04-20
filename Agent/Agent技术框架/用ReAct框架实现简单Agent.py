import os

# 设置环境变量
os.environ["DASHSCOPE_API_KEY"] = "sk-51b422ad7151406b8c3ddb1ce0a424ba"  # Qwen模型的API密钥
os.environ["SERPAPI_API_KEY"] = "97db7da7af0aa8b813d9ecca8595b1b9c4ed253b2d9bcaa15ec53a0f3568a6ea"

# 导入LangChain Hub - 使用langsmith SDK（推荐）
from langsmith import Client as LangSmithClient

# 从LangChain Hub中获取ReAct的提示
ls_client = LangSmithClient()
prompt = ls_client.pull_prompt("hwchase17/react")
print("ReAct Prompt:")
print(prompt)

"""
{
  "input_variables": [
    "agent_scratchpad",
    "input",
    "tool_names",
    "tools"
  ],
  "input_types": {},
  "partial_variables": {},
  "metadata": {
    "lc_hub_owner": "hwchase17",
    "lc_hub_repo": "react",
    "lc_hub_commit_hash": "d15fe3c426f1c4b3f37c9198853e4a86e20c425ca7f4752ec0c9b0e97ca7ea4d"
  },
  "template": "Answer the following questions as best you can. You have access to the following tools:\n\n{tools}\n\nUse the following format:\n\nQuestion: the input question you must answer\nThought: you should always think about what to do\nAction: the action to take, should be one of [{tool_names}]\nAction Input: the input to the action\nObservation: the result of the action\n... (this Thought/Action/Action Input/Observation can repeat N times)\nThought: I now know the final answer\nFinal Answer: the final answer to the original input question\n\nBegin!\n\nQuestion: {input}\nThought:{agent_scratchpad}"
}
"""

# 导入Qwen模型 - 使用ChatOpenAI兼容接口
from langchain_openai import ChatOpenAI

# 选择要使用的大模型，使用Qwen模型（通过OpenAI兼容接口）
llm = ChatOpenAI(
    model="qwen-max",
    openai_api_key=os.environ["DASHSCOPE_API_KEY"],
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 导入SerpAPIWrapper即工具包
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import Tool

# 实例化SerpAPIWrapper
search = SerpAPIWrapper()

# 准备工具列表
tools = [
    Tool(
        name="Search",
        func=search.run,
        description="当大模型没有相关知识时，用于搜索知识"
    ),
]

# 导入create_react_agent功能 - 使用langchain_classic（兼容旧版API）
from langchain_classic.agents import create_react_agent, AgentExecutor

# 构建ReAct Agent
agent = create_react_agent(llm, tools, prompt)

# 创建Agent执行器并传入Agent和工具
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 调用AgentExecutor
result = agent_executor.invoke({"input": "当前Agent最新研究进展是什么？"})
print("\n最终结果:")
print(result["output"])