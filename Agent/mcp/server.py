import sys
from mcp.server.fastmcp import FastMCP

# 1. 初始化 FastMCP Server
# 这里的名称会在 Client 连接时作为标识
mcp = FastMCP("MyDemoServer")


# 2. 定义一个 Tool (工具调用)
# 使用 @mcp.tool() 装饰器，SDK 会自动提取函数名、参数类型声明和 docstring 转化为 JSON Schema
@mcp.tool()
def fetch_user_data(user_id: int) -> str:
    """根据 User ID 获取用户的模拟数据库信息"""
    # 在真实业务中，这里可以是你的 MySQL 或 Vector DB 查询逻辑
    mock_db = {
        1: {"name": "Alice", "role": "Admin", "status": "Active"},
        2: {"name": "Bob", "role": "Developer", "status": "Inactive"}
    }

    user = mock_db.get(user_id)
    if user:
        return f"User Found: {user['name']}, Role: {user['role']}"
    return "Error: User not found."


@mcp.tool()
def calculate_system_load(cores: int, active_threads: int) -> float:
    """模拟计算当前系统的负载率"""
    if cores <= 0:
        return 0.0
    return round((active_threads / (cores * 2)) * 100, 2)


if __name__ == "__main__":
    # 3. 运行 Server
    # 默认使用 stdio (标准输入输出) 进行进程间通信，这是 MCP 最常用的本地交互方式
    print("Starting MCP Server...", file=sys.stderr)  # 注意：日志必须打印到 stderr，因为 stdout 被用作协议通信
    mcp.run()