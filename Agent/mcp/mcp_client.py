import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # 1. 配置 Server 启动参数
    # 这里告诉 Client 去运行我们刚才写的 server.py
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )

    print("🔌 正在连接到 MCP Server...")

    # 2. 通过 stdio 建立连接
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 3. 初始化协议 (握手)
            await session.initialize()
            print("✅ 握手成功！")

            # 4. 获取 Server 提供的工具列表
            tools_response = await session.list_tools()
            print("\n🛠️ Server 提供的可用工具:")
            for tool in tools_response.tools:
                print(f" - {tool.name}: {tool.description}")

            # 5. 调用指定的工具 (Tool Calling)
            print("\n🚀 开始调用工具: fetch_user_data(user_id=1)")
            result1 = await session.call_tool(
                name="fetch_user_data",
                arguments={"user_id": 1}
            )
            # 解析并打印结果
            # result.content 通常是一个列表，包含文本或图像等多种模态的数据
            print(f"📥 结果: {result1.content[0].text}")

            print("\n🚀 开始调用工具: calculate_system_load(cores=8, active_threads=12)")
            result2 = await session.call_tool(
                name="calculate_system_load",
                arguments={"cores": 8, "active_threads": 12}
            )
            print(f"📥 结果: {result2.content[0].text}%")


if __name__ == "__main__":
    # 运行异步客户端
    asyncio.run(main())