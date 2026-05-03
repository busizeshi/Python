from __future__ import annotations

# 导入正则库，用于做简单的路由规则判断。
import re
# 导入 dataclass，构建结构化返回值。
from dataclasses import dataclass
# 导入 Literal，用于约束路由返回值只能是固定集合。
from typing import Literal

# 导入我们封装好的千问客户端。
from .llm_qwen import QwenClient


# 统一的 Agent 执行结果结构。
@dataclass(slots=True)
class TaskResult:
    # 当前结果来自哪个 Agent。
    agent: str
    # Agent 输出的正文内容。
    output: str
    # 置信度（演示用数值）。
    confidence: float


# Agent 基类，约束每个子类都要实现 run 方法。
class BaseAgent:
    # Agent 名称字段。
    name: str

    # 执行入口。
    def run(self, query: str) -> TaskResult:
        # 基类不提供实现，子类必须覆盖。
        raise NotImplementedError


# 数学 Agent：负责处理简单算式。
class MathAgent(BaseAgent):
    # 固定的 Agent 标识。
    name = "math_agent"

    # 构造函数。
    def __init__(self, qwen: QwenClient) -> None:
        # 保存千问客户端，供后续可选调用。
        self.qwen = qwen

    # 执行函数。
    def run(self, query: str) -> TaskResult:
        # 先给一个稳定的本地回退答案（离线也能跑）。
        local_output: str
        # 去掉常见指令前缀后，尝试解析表达式。
        expr = query.replace("calculate", "").replace("计算", "").strip()
        # 若用户没给表达式，则给默认值 0。
        expr = expr or "0"
        # 使用异常保护，避免非法表达式导致崩溃。
        try:
            # 仅用于教学演示：受限 eval。
            value = eval(expr, {"__builtins__": {}}, {})  # noqa: S307
            # 本地成功结果。
            local_output = f"数学结果：{value}"
            # 本地成功时置信度较高。
            local_conf = 0.95
        except Exception as exc:
            # 本地失败结果。
            local_output = f"数学解析失败：{exc}"
            # 本地失败时置信度较低。
            local_conf = 0.2

        # 组装系统提示词，约束模型角色。
        system_prompt = "你是数学助手，请给出简洁、准确、可核对的结果。"
        # 组装用户提示词。
        user_prompt = f"请计算并解释：{query}"
        # 调用千问；未配置 key 时会自动返回 fallback。
        llm_resp = self.qwen.chat(system_prompt, user_prompt, local_output)
        # 根据是否远程模型，微调置信度。
        confidence = 0.98 if llm_resp.used_remote_model else local_conf
        # 返回统一结构。
        return TaskResult(self.name, llm_resp.text, confidence)


# 研究 Agent：负责给出结构化分析。
class ResearchAgent(BaseAgent):
    # Agent 标识。
    name = "research_agent"

    # 构造函数。
    def __init__(self, qwen: QwenClient) -> None:
        # 保存千问客户端。
        self.qwen = qwen

    # 执行函数。
    def run(self, query: str) -> TaskResult:
        # 本地离线回退文本。
        local_summary = (
            "研究摘要：先拆解需求，再列出假设，定义评估指标，最后识别风险与缓解方案。"
        )
        # 系统提示词：约束输出风格。
        system_prompt = "你是资深架构研究员，请输出条理清晰的工程分析。"
        # 用户提示词：输入任务。
        user_prompt = f"请给出主题的工程分析：{query}"
        # 调用千问（自动回退）。
        llm_resp = self.qwen.chat(system_prompt, user_prompt, local_summary)
        # 远程模型和本地回退置信度。
        confidence = 0.9 if llm_resp.used_remote_model else 0.86
        # 返回统一结构。
        return TaskResult(self.name, llm_resp.text, confidence)


# 评审 Agent：负责对已有答案做质量审查。
class CriticAgent(BaseAgent):
    # Agent 标识。
    name = "critic_agent"

    # 构造函数。
    def __init__(self, qwen: QwenClient) -> None:
        # 保存千问客户端。
        self.qwen = qwen

    # 执行函数。
    def run(self, query: str) -> TaskResult:
        # 本地回退审查意见。
        local_feedback = "评审意见：补充边界情况、增加可观测日志、完善异常处理与回归验证。"
        # 系统提示词。
        system_prompt = "你是代码评审专家，请给出严谨、可执行的改进建议。"
        # 用户提示词。
        user_prompt = f"请评审以下内容并提出改进建议：{query}"
        # 调用千问（自动回退）。
        llm_resp = self.qwen.chat(system_prompt, user_prompt, local_feedback)
        # 置信度设置。
        confidence = 0.88 if llm_resp.used_remote_model else 0.8
        # 返回统一结构。
        return TaskResult(self.name, llm_resp.text, confidence)


# Supervisor 负责做“路由决策”：把请求交给 math 或 research。
class Supervisor:
    # 正则：匹配“数字 运算符 数字”的基础算式。
    _expr_pattern = re.compile(r"\d+\s*[+\-*/]\s*\d+")

    # 路由函数。
    def route(self, query: str) -> Literal["math", "research"]:
        # 转小写，便于统一匹配。
        lowered = query.lower()
        # 如果包含计算关键词或命中算式模式，就走数学分支。
        if (
            "calculate" in lowered
            or "计算" in lowered
            or self._expr_pattern.search(lowered)
        ):
            return "math"
        # 其余默认走研究分支。
        return "research"


# 对外提供统一初始化入口，确保多个 Agent 共享同一个 QwenClient。
def build_agents() -> tuple[Supervisor, MathAgent, ResearchAgent, CriticAgent]:
    # 创建千问客户端。
    qwen = QwenClient()
    # 返回 supervisor 和三个 specialist。
    return Supervisor(), MathAgent(qwen), ResearchAgent(qwen), CriticAgent(qwen)
