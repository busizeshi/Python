from __future__ import annotations

# 这里导入 os，用于读取环境变量（比如 API Key、模型名等配置）。
import os
# 这里导入 dataclass，便于定义结构清晰的数据对象。
from dataclasses import dataclass
# 这里导入 Optional，表示某些字段可以为空。
from typing import Optional

# 这里导入 OpenAI 官方 Python SDK。
# DashScope 提供 OpenAI 兼容接口，所以我们可以直接复用这个客户端。
from openai import OpenAI


# 这个数据类表示一次模型调用的结果。
@dataclass(slots=True)
class LLMResponse:
    # 模型返回的文本内容。
    text: str
    # 是否使用了真实远程模型（True）还是本地回退（False）。
    used_remote_model: bool


# 这个类负责统一封装“调用阿里云千问”的逻辑。
class QwenClient:
    # 构造函数：初始化客户端配置。
    def __init__(self) -> None:
        # 从环境变量读取 API Key。
        self.api_key: str = os.getenv("DASHSCOPE_API_KEY", "").strip()
        # 从环境变量读取模型名，给一个默认值 qwen-plus。
        self.model: str = os.getenv("QWEN_MODEL", "qwen-turbo").strip() or "qwen-plus"
        # DashScope 的 OpenAI 兼容 base_url。
        self.base_url: str = os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ).strip()
        # 如果没有配置 key，就不创建远程客户端。
        self._client: Optional[OpenAI] = None
        # 只有 key 存在时，才初始化 OpenAI 客户端。
        if self.api_key:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    # 这个方法用于判断：当前是否已经具备远程调用条件。
    def is_enabled(self) -> bool:
        # 只要 _client 不为空，就表示可远程调用。
        return self._client is not None

    # 这个方法统一执行聊天补全。
    def chat(self, system_prompt: str, user_prompt: str, fallback_text: str) -> LLMResponse:
        # 如果没有配置好远程模型，就直接返回本地回退内容。
        if not self._client:
            return LLMResponse(text=fallback_text, used_remote_model=False)

        # 进入异常保护，避免网络波动导致程序中断。
        try:
            # 调用 OpenAI 兼容接口。
            resp = self._client.chat.completions.create(
                # 指定模型名，例如 qwen-plus、qwen-max。
                model=self.model,
                # messages 按角色组织上下文。
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                # 控制采样温度，低一些更稳定。
                temperature=0.2,
            )
            # 从响应里取第一条候选内容。
            text = (resp.choices[0].message.content or "").strip()
            # 如果模型返回了空文本，依然使用 fallback。
            if not text:
                return LLMResponse(text=fallback_text, used_remote_model=False)
            # 正常返回模型结果。
            return LLMResponse(text=text, used_remote_model=True)
        except Exception:
            # 任意异常都降级到本地回退，确保学习项目始终可运行。
            return LLMResponse(text=fallback_text, used_remote_model=False)
