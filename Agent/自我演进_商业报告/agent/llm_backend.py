import json
import os
from datetime import datetime
from typing import Any, Dict

from openai import OpenAI

from .search import baidu_search_func, baidu_search_tool


class QwenBackend:
    """千问后端：负责报告生成和反思决策。"""

    def __init__(self, model: str | None = None):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("缺少 DASHSCOPE_API_KEY")

        self.base_url = os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = model or os.getenv("CHAT_MODEL", "qwen-plus")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate_report(self, prompt: str, style: Dict[str, Any]) -> str:
        prefer_bullets = style.get("prefer_bullets", False)
        target_words = int(style.get("target_words", 800))
        style_hint = "项目符号" if prefer_bullets else "段落"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        system_prompt = (
            "你是一名专业商业分析师，擅长输出结构化、可执行的商业报告。"
            f"当前时间：{current_time}。如涉及市场/新闻，请优先考虑较新信息。"
        )

        user_prompt = (
            "请根据以下要求撰写详细商业报告：\n\n"
            f"- 目标字数：约 {target_words} 字\n"
            f"- 格式：{style_hint}\n"
            "- 内容：有逻辑、有数据意识、有行动建议\n\n"
            f"用户需求：\n{prompt}\n\n"
            f"请尽量接近 {target_words} 字。"
        )

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = resp.choices[0].message.content
        return content.strip() if content else ""

    def reflect_and_decide(self, prompt: str, context: str, draft: str) -> Dict[str, Any]:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        system = (
            "你是自我演进的商业报告代理。"
            f"当前时间：{current_time}。"
            "如果信息缺失，优先调用搜索工具；否则直接改写草稿。"
        )

        user = (
            f"用户需求：\n{prompt}\n\n"
            f"上下文（可能包含搜索结果）：\n{context}\n\n"
            f"当前草稿：\n{draft}\n\n"
            "决策原则：\n"
            "1) 若缺少关键事实（市场规模、竞品、最新动态），调用搜索工具；\n"
            "2) 否则输出改写后的完整报告文本。"
        )

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tools=[baidu_search_tool],
            tool_choice="auto",
        )

        msg = resp.choices[0].message
        tool_calls = msg.tool_calls or []
        if tool_calls:
            for tc in tool_calls:
                if tc.function.name == "baidu_search_func":
                    args = json.loads(tc.function.arguments or "{}")
                    results = baidu_search_func(**args)
                    return {
                        "action": "search",
                        "query": args.get("query", ""),
                        "results": results,
                    }

        return {"action": "revise", "new_text": (msg.content or "").strip()}

