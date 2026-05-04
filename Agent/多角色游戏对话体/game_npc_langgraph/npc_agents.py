from langchain_openai import ChatOpenAI
import os

# 定义NPC人设
npc_profiles = {
    "村长": """你是村长，年长睿智，喜欢讲故事和给建议。\n当有人问村里有哪些NPC时，你会介绍三位主要居民：\n1. 村长（你自己）：负责村庄管理和提供建议\n2. 铁匠：擅长打造和修理武器装备\n3. 药师：懂得草药和治疗，帮助村民解决健康问题\n只介绍这三位，不要编造其他角色。\n重要：直接回复内容，不要在前面加“村长：”等角色标识。""",
    "铁匠": """你是铁匠，擅长打造和修理武器，说话粗犷。\n你专注于武器装备相关话题。\n重要：直接回复内容，不要在前面加“铁匠：”等角色标识。""",
    "药师": """你是药师，懂草药和治疗，语气温和。\n你专注于健康和治疗相关话题。\n重要：直接回复内容，不要在前面加“药师：”等角色标识。""",
}

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "qwen-turbo"),
    api_key=os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
)


def npc_node(npc_name: str):
    """返回一个NPC节点函数"""

    def node(state):
        user_input = state["input"]
        chat_history = state.get("chat_history", [])

        messages = [{"role": "system", "content": npc_profiles[npc_name]}]

        if chat_history:
            recent_history = chat_history[-20:]
            messages.extend(recent_history)

        messages.append({"role": "user", "content": user_input})

        resp = llm.invoke(messages)
        return {"output": f"{npc_name}: {resp.content}"}

    return node
