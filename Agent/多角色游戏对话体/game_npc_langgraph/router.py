from langchain_openai import ChatOpenAI
import os
from datetime import datetime

llm_router = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "qwen-turbo"),
    api_key=os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
)


def route_node(state):
    """用LLM决定分配给哪个NPC"""
    user_input = state["input"]
    chat_history = state.get("chat_history", [])
    debug = os.getenv("ROUTER_DEBUG", "1") == "1"

    def log(msg: str):
        if debug:
            print(f"[router][{datetime.now().strftime('%H:%M:%S')}] {msg}")

    system_prompt = """你是一个游戏调度器。根据玩家输入和对话历史，选择最合适的NPC来回答。
可选NPC：
- 村长：村庄管理、历史故事、一般建议和信息
- 铁匠：武器装备、打造修理、战斗相关
- 药师：治疗、草药、健康相关

规则：
1. 只能选择一个NPC
2. 直接输出NPC名字，不要多余文字
3. 要考虑上下文，相关话题可连续选择同一NPC
4. 如果问题较泛或跨领域，默认选择村长
"""

    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        recent_history = chat_history[-10:]
        messages.extend(recent_history)
    else:
        recent_history = []

    messages.append({"role": "user", "content": user_input})

    log(f"user_input={repr(user_input)}")
    log(f"chat_history_total={len(chat_history)}, recent_used={len(recent_history)}")
    log(f"messages_count={len(messages)}")

    resp = llm_router.invoke(messages)
    raw_output = resp.content if resp and hasattr(resp, "content") else ""
    raw_output = raw_output or ""
    chosen_npc = raw_output.strip()

    log(f"llm_raw_output={repr(raw_output)}")
    log(f"llm_stripped_output={repr(chosen_npc)}")

    valid_npcs = ["村长", "铁匠", "药师"]

    if chosen_npc in valid_npcs:
        final_npc = chosen_npc
        reason = "exact_match"
    elif "药师" in chosen_npc:
        final_npc = "药师"
        reason = "fuzzy_match_药师"
    elif "铁匠" in chosen_npc:
        final_npc = "铁匠"
        reason = "fuzzy_match_铁匠"
    elif "村长" in chosen_npc:
        final_npc = "村长"
        reason = "fuzzy_match_村长"
    else:
        final_npc = "村长"
        reason = "fallback_default"

    if final_npc not in valid_npcs:
        final_npc = "村长"
        reason = "safety_fallback_default"

    if final_npc != chosen_npc:
        log(f"route_adjusted_from={repr(chosen_npc)} to={repr(final_npc)}")
    log(f"route_final={final_npc}, reason={reason}")

    return {"npc_targets": [final_npc]}
