from __future__ import annotations

# ThreadPoolExecutor 用于并行模式。
from concurrent.futures import ThreadPoolExecutor
# dataclass 用于定义结构化 Agent 包装器。
from dataclasses import dataclass
# count 用于生成自增任务 ID。
from itertools import count
# Callable 用于声明 handler 函数类型。
from typing import Callable

# 导入三个业务 Agent。
from ..agents import CriticAgent, MathAgent, ResearchAgent, build_agents
# 导入 A2A 协议对象。
from .protocol import A2AMessage, A2ATask, AgentCard, Artifact


# A2AAgent：把“能力说明 + 执行函数”绑定在一起。
@dataclass(slots=True)
class A2AAgent:
    # Agent 能力卡片。
    card: AgentCard
    # 具体执行函数，输入 goal，输出文本。
    handler: Callable[[str], str]

    # 执行任务的方法。
    def execute(self, task: A2ATask) -> A2ATask:
        # 任务状态切换到 running。
        task.start()
        # 异常保护，保证失败可观测。
        try:
            # 调用实际处理逻辑。
            output = self.handler(task.goal)
            # 记录 assistant 消息。
            task.messages.append(A2AMessage(role="assistant", content=output))
            # 产出 artifact 并标记成功。
            task.succeed(Artifact(name=f"{self.card.name}_result", content=output))
        except Exception as exc:  # pragma: no cover
            # 异常时标记失败。
            task.fail(str(exc))
        # 返回更新后的任务。
        return task


# Orchestrator：统一封装四种典型 A2A 编排模式。
class A2AOrchestrator:
    # 构造函数。
    def __init__(self) -> None:
        # 初始化任务编号生成器。
        self._counter = count(1)
        # 复用同一套底层 Agent 实例（其中已包含 Qwen 能力）。
        _, math_agent, research_agent, critic_agent = build_agents()

        # 注册数学 Agent。
        self.math = A2AAgent(
            AgentCard("数学智能体", "处理算术表达式", ["math"], "local://math"),
            lambda goal: math_agent.run(goal).output,
        )
        # 注册研究 Agent。
        self.research = A2AAgent(
            AgentCard("研究智能体", "输出工程分析摘要", ["research"], "local://research"),
            lambda goal: research_agent.run(goal).output,
        )
        # 注册评审 Agent。
        self.critic = A2AAgent(
            AgentCard("评审智能体", "审查答案质量", ["review"], "local://critic"),
            lambda goal: critic_agent.run(goal).output,
        )

    # 创建新任务对象。
    def _new_task(self, requester: str, assignee: str, goal: str) -> A2ATask:
        # 生成递增 ID。
        task_id = f"task-{next(self._counter):04d}"
        # 返回任务对象。
        return A2ATask(task_id=task_id, requester=requester, assignee=assignee, goal=goal)

    # 模式一：顺序模式（Sequential）。
    def run_sequential(self, query: str) -> dict:
        # 第一步：研究。
        t1 = self._new_task("编排器", self.research.card.name, query)
        out1 = self.research.execute(t1)

        # 第二步：把研究结果交给评审。
        t2 = self._new_task("编排器", self.critic.card.name, out1.artifacts[-1].content)
        out2 = self.critic.execute(t2)

        # 返回统一结果。
        return {
            "mode": "顺序",
            "tasks": [out1, out2],
            "final": out2.artifacts[-1].content,
        }

    # 模式二：并行模式（Parallel）。
    def run_parallel(self, query: str) -> dict:
        # 准备两个并行任务：数学 + 研究。
        t1 = self._new_task("编排器", self.math.card.name, query)
        t2 = self._new_task("编排器", self.research.card.name, query)

        # 创建线程池并发执行。
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(self.math.execute, t1)
            f2 = pool.submit(self.research.execute, t2)
            out1 = f1.result()
            out2 = f2.result()

        # 汇总并行结果。
        final = (
            "并行汇总：\n"
            f"- {out1.assignee}: {out1.artifacts[-1].content}\n"
            f"- {out2.assignee}: {out2.artifacts[-1].content}"
        )
        # 返回结果。
        return {"mode": "并行", "tasks": [out1, out2], "final": final}

    # 模式三：条件模式（Conditional）。
    def run_conditional(self, query: str) -> dict:
        # 简单规则：出现计算关键词或运算符就走数学。
        choose_math = any(token in query.lower() for token in ["calculate", "计算", "+", "-", "*", "/"])
        # 根据规则选择 Agent。
        chosen = self.math if choose_math else self.research
        # 创建并执行任务。
        task = self._new_task("编排器", chosen.card.name, query)
        out = chosen.execute(task)
        # 返回结果。
        return {
            "mode": "条件",
            "chosen": chosen.card.name,
            "tasks": [out],
            "final": out.artifacts[-1].content,
        }

    # 模式四：流水线模式（Pipeline）。
    def run_pipeline(self, query: str) -> dict:
        # 阶段 1：研究。
        t1 = self._new_task("编排器", self.research.card.name, query)
        out1 = self.research.execute(t1)

        # 阶段 2：评审研究结果。
        t2 = self._new_task("编排器", self.critic.card.name, out1.artifacts[-1].content)
        out2 = self.critic.execute(t2)

        # 阶段 3：做一个可验证数学检查（演示“可核对步骤”）。
        t3 = self._new_task("编排器", self.math.card.name, "calculate 20 + 22")
        out3 = self.math.execute(t3)

        # 汇总流水线输出。
        final = (
            "流水线输出：\n"
            f"1) 研究={out1.artifacts[-1].content}\n"
            f"2) 评审={out2.artifacts[-1].content}\n"
            f"3) 校验={out3.artifacts[-1].content}"
        )
        # 返回结果。
        return {"mode": "流水线", "tasks": [out1, out2, out3], "final": final}
