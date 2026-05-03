import asyncio
import json
import os
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 1. 核心修改：将 OpenAI 客户端指向通义千问的兼容服务地址
# 千问 API 完美兼容 OpenAI 的 SDK，只需替换 base_url 和 api_key
llm_client = AsyncOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


async def qwen_mcp_agent():
    # 启动并连接你在上一步写的 server.py
    server_params = StdioServerParameters(command="python", args=["server.py"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 2. 从 MCP Server 获取可用工具
            mcp_tools_response = await session.list_tools()

            # 3. 将 MCP 工具转换为千问（OpenAI 兼容格式）的 tools 结构
            qwen_tools = []
            for tool in mcp_tools_response.tools:
                qwen_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            # 4. 用户输入自然语言
            messages = [{"role": "user",
                         "content": "帮我看看ID为2的用户的角色是什么，顺便算一下目前16核处理器，8个线程活跃情况下的系统负载。"}]

            print("🗣️ 正在请求千问大模型思考...")

            # 5. 核心修改：指定千问的模型版本（推荐使用 qwen-turbo 或 qwen-plus，工具调用能力最强）
            response = await llm_client.chat.completions.create(
                model="qwen-turbo",
                messages=messages,
                tools=qwen_tools
            )

            message = response.choices[0].message
            messages.append(message)

            # 6. 处理千问返回的工具调用请求
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"🤖 千问决定调用工具: {tool_name}({tool_args})")

                    # 7. 使用 MCP Client 执行真实逻辑
                    mcp_result = await session.call_tool(tool_name, tool_args)
                    result_text = mcp_result.content[0].text
                    print(f"✅ 工具执行结果: {result_text}")

                    # 8. 将结果封装成 tool message 喂回给千问
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": result_text
                    })

                # 9. 第二次调用千问，生成最终回复
                print("🗣️ 正在请求千问总结...")
                final_response = await llm_client.chat.completions.create(
                    model="qwen-turbo",
                    messages=messages
                )
                print(f"\n🎉 最终回答:\n{final_response.choices[0].message.content}")
            else:
                print(f"\n🎉 千问直接回答:\n{message.content}")


if __name__ == "__main__":
    asyncio.run(qwen_mcp_agent())