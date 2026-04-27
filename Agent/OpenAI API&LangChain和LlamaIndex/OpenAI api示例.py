"""
OpenAI API 详细学习示例 - 使用通义千问（Qwen）模型

前置准备:
1. 安装: pip install openai
2. 获取 API Key: 前往 https://dashscope.console.aliyun.com/ 注册并获取
3. 千问 API 文档: https://help.aliyun.com/zh/model-studio/developer-reference/api

千问模型兼容 OpenAI API，只需设置:
- base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
- api_key = "你的千问API Key"

常用千问模型:
- qwen-plus: 均衡模型，推荐日常使用
- qwen-turbo: 速度快，成本低
- qwen-max: 最强推理能力，适合复杂任务
- qwen-long: 支持超长上下文（100万字）
"""

import os
from openai import OpenAI

# ============================================================
# 1. 初始化客户端
# ============================================================
print("=" * 60)
print("1. 初始化客户端")
print("=" * 60)

# 方式一：直接传入 API Key
# client = OpenAI(
#     api_key="sk-xxx",  # 替换为你的千问 API Key
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
# )

# 方式二：从环境变量读取（推荐）
# 设置环境变量: export DASHSCOPE_API_KEY="sk-xxx" (Linux/Mac)
#            或 set DASHSCOPE_API_KEY=sk-xxx (Windows)
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY", "sk-51b422ad7151406b8c3ddb1ce0a424ba"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

MODEL = "qwen-plus"  # 可替换为 qwen-turbo / qwen-max / qwen-long


# ============================================================
# 2. 基础对话 - 简单问答
# ============================================================
print("\n" + "=" * 60)
print("2. 基础对话 - 简单问答")
print("=" * 60)

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "你是一个 helpful 的AI助手。"},
        {"role": "user", "content": "请用一句话解释什么是人工智能？"},
    ],
    temperature=0.7,   # 控制随机性，0-1之间，越高越有创造性
    max_tokens=500,    # 最大生成令牌数
)

# 查看完整响应结构
print(f"模型: {response.model}")
print(f"完成原因: {response.choices[0].finish_reason}")
print(f"用量: {response.usage}")
print(f"回答: {response.choices[0].message.content}")


# ============================================================
# 3. 多轮对话 - 保持上下文
# ============================================================
print("\n" + "=" * 60)
print("3. 多轮对话 - 保持上下文")
print("=" * 60)

messages = [
    {"role": "system", "content": "你是一个Python编程老师，用简洁的方式教学。"},
    {"role": "user", "content": "什么是列表推导式？"},
]

# 第一轮
response1 = client.chat.completions.create(model=MODEL, messages=messages)
answer1 = response1.choices[0].message.content
messages.append({"role": "assistant", "content": answer1})
print(f"Q1: 什么是列表推导式？")
print(f"A1: {answer1[:200]}...\n")

# 第二轮（模型能记住上文）
messages.append({"role": "user", "content": "能给我一个实际使用的例子吗？"})
response2 = client.chat.completions.create(model=MODEL, messages=messages)
answer2 = response2.choices[0].message.content
messages.append({"role": "assistant", "content": answer2})
print(f"Q2: 能给我一个实际使用的例子吗？")
print(f"A2: {answer2[:200]}...")


# ============================================================
# 4. 流式输出 - 打字机效果
# ============================================================
print("\n" + "=" * 60)
print("4. 流式输出 - 打字机效果")
print("=" * 60)

stream = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "user", "content": "写一首关于春天的四行诗"},
    ],
    stream=True,  # 开启流式输出
)

print("回答: ", end="", flush=True)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()  # 换行


# ============================================================
# 5. 结构化输出 - JSON 格式
# ============================================================
print("\n" + "=" * 60)
print("5. 结构化输出 - JSON 格式")
print("=" * 60)

import json

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "你只输出JSON格式，不要输出其他文字。"},
        {"role": "user", "content": "请生成3个城市的天气信息，包含城市名、温度、天气状况"},
    ],
    response_format={"type": "json_object"},  # 强制JSON输出
)

data = json.loads(response.choices[0].message.content)
print(json.dumps(data, ensure_ascii=False, indent=2))


# ============================================================
# 6. Function Calling - 函数调用
# ============================================================
print("\n" + "=" * 60)
print("6. Function Calling - 函数调用")
print("=" * 60)


# 定义工具（函数描述）
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，如北京、上海"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "温度单位"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_news",
            "description": "搜索最新新闻",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "新闻主题"},
                    "count": {"type": "integer", "description": "返回条数"},
                },
                "required": ["topic"],
            },
        },
    },
]

# 模拟函数实现
def get_weather(city, unit="celsius"):
    """模拟获取天气"""
    weather_data = {
        "北京": {"temp": 22, "condition": "晴", "unit": unit},
        "上海": {"temp": 25, "condition": "多云", "unit": unit},
        "广州": {"temp": 30, "condition": "雷阵雨", "unit": unit},
    }
    info = weather_data.get(city, {"temp": 20, "condition": "未知", "unit": unit})
    return f"{city}当前{info['condition']}，{info['temp']}°{info['unit'][0].upper()}"

def search_news(topic, count=3):
    """模拟搜索新闻"""
    return f"找到{count}条关于'{topic}'的新闻（模拟数据）"

# 执行函数调用
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "user", "content": "北京今天天气怎么样？"},
    ],
    tools=tools,
)

choice = response.choices[0]
if choice.message.tool_calls:
    for tool_call in choice.message.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        print(f"模型决定调用函数: {func_name}")
        print(f"参数: {func_args}")

        # 执行对应函数
        if func_name == "get_weather":
            result = get_weather(**func_args)
        elif func_name == "search_news":
            result = search_news(**func_args)
        else:
            result = "未知函数"
        print(f"函数返回: {result}")

        # 把结果回传给模型，获取最终回答
        messages_fc = [
            {"role": "user", "content": "北京今天天气怎么样？"},
            choice.message,  # 模型的函数调用
            {"role": "tool", "tool_call_id": tool_call.id, "content": result},
        ]
        final_response = client.chat.completions.create(
            model=MODEL, messages=messages_fc, tools=tools,
        )
        print(f"最终回答: {final_response.choices[0].message.content}")


# ============================================================
# 7. 视觉理解 - 图片识别（多模态）
# ============================================================
print("\n" + "=" * 60)
print("7. 视觉理解 - 图片识别（需要 qwen-vl 系列模型）")
print("=" * 60)

# 注意: 需要使用 qwen-vl-plus 或 qwen-vl-max 模型
# response = client.chat.completions.create(
#     model="qwen-vl-plus",
#     messages=[
#         {
#             "role": "user",
#             "content": [
#                 {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
#                 {"type": "text", "text": "请描述这张图片的内容"},
#             ],
#         }
#     ],
# )
# print(response.choices[0].message.content)
print("（如需使用视觉能力，请取消上方代码注释并使用 qwen-vl-plus 模型）")


# ============================================================
# 8. 错误处理最佳实践
# ============================================================
print("\n" + "=" * 60)
print("8. 错误处理最佳实践")
print("=" * 60)

from openai import APIError, APITimeoutError, RateLimitError, AuthenticationError


def safe_chat(prompt, max_retries=3):
    """带重试和错误处理的对话函数"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                timeout=30,  # 超时时间（秒）
            )
            return response.choices[0].message.content

        except AuthenticationError:
            return "错误: API Key 无效，请检查你的 DASHSCOPE_API_KEY"
        except RateLimitError:
            print(f"请求频率超限，等待后重试 (尝试 {attempt + 1}/{max_retries})")
            import time
            time.sleep(2 ** attempt)  # 指数退避
        except APITimeoutError:
            print(f"请求超时 (尝试 {attempt + 1}/{max_retries})")
        except APIError as e:
            print(f"API 错误: {e} (尝试 {attempt + 1}/{max_retries})")
        except Exception as e:
            return f"未知错误: {e}"

    return "多次重试后仍失败"


result = safe_chat("你好，简单打个招呼即可")
print(f"安全调用结果: {result}")


# ============================================================
# 9. 常用参数详解
# ============================================================
print("\n" + "=" * 60)
print("9. 常用参数详解")
print("=" * 60)

params_explanation = """
常用参数说明:

- temperature (0~2): 控制输出随机性
  0 = 确定性最高，适合代码生成、事实问答
  0.7 = 默认值，平衡创造性和准确性
  1.0+ = 更有创造性，适合创意写作

- max_tokens: 最大生成长度
  不包括输入prompt，仅计算输出部分
  千问-plus 最大支持约 8000 tokens

- top_p (0~1): 核采样参数
  控制模型从多少个最高概率的词中选择
  通常与 temperature 二选一调整

- stop: 停止词
  遇到指定字符串时停止生成
  可以是字符串或字符串列表

- presence_penalty (-2~2): 存在惩罚
  正值让模型更可能谈论新话题
  避免重复相同主题

- frequency_penalty (-2~2): 频率惩罚
  正值降低重复使用相同词句的概率
"""
print(params_explanation)


# ============================================================
# 10. Token 计算
# ============================================================
print("\n" + "=" * 60)
print("10. Token 计算")
print("=" * 60)

# 千问 DashScope 支持通过 API 获取 token 用量
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "你好"}],
)
print(f"输入 tokens (prompt): {response.usage.prompt_tokens}")
print(f"输出 tokens (completion): {response.usage.completion_tokens}")
print(f"总 tokens: {response.usage.total_tokens}")
