from __future__ import annotations

# dataclass/field 用于定义协议对象并配置默认值工厂。
from dataclasses import dataclass, field
# UTC + datetime 用于记录标准化时间戳。
from datetime import UTC, datetime
# Enum 用于约束任务状态集合。
from enum import Enum


# A2A 任务状态枚举：描述任务生命周期。
class TaskStatus(str, Enum):
    # 任务刚创建，还未执行。
    CREATED = "created"
    # 任务正在执行中。
    RUNNING = "running"
    # 任务成功完成。
    SUCCEEDED = "succeeded"
    # 任务执行失败。
    FAILED = "failed"


# AgentCard：用于描述某个 Agent 的能力和入口。
@dataclass(slots=True)
class AgentCard:
    # Agent 名称（唯一标识）。
    name: str
    # Agent 的能力说明。
    description: str
    # 技能标签列表。
    skills: list[str]
    # Agent 访问端点（本地/远程地址）。
    endpoint: str


# A2A 消息对象：记录任务过程中的对话/日志。
@dataclass(slots=True)
class A2AMessage:
    # 消息角色，例如 user / assistant / system。
    role: str
    # 消息正文。
    content: str
    # 创建时间（UTC）。
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# Artifact：任务产物，便于下游继续处理。
@dataclass(slots=True)
class Artifact:
    # 产物名称。
    name: str
    # 产物内容。
    content: str


# A2ATask：A2A 调用中的核心载体。
@dataclass(slots=True)
class A2ATask:
    # 任务唯一 ID。
    task_id: str
    # 请求方标识。
    requester: str
    # 执行方标识。
    assignee: str
    # 任务目标描述。
    goal: str
    # 任务状态，默认 created。
    status: TaskStatus = TaskStatus.CREATED
    # 消息列表，默认空列表。
    messages: list[A2AMessage] = field(default_factory=list)
    # 产物列表，默认空列表。
    artifacts: list[Artifact] = field(default_factory=list)

    # 标记任务开始执行。
    def start(self) -> None:
        # 更新状态为 running。
        self.status = TaskStatus.RUNNING

    # 标记任务成功，并保存产物。
    def succeed(self, artifact: Artifact) -> None:
        # 先保存产物。
        self.artifacts.append(artifact)
        # 再更新状态为 succeeded。
        self.status = TaskStatus.SUCCEEDED

    # 标记任务失败，并记录失败原因。
    def fail(self, reason: str) -> None:
        # 追加一条系统消息，便于排查。
        self.messages.append(A2AMessage(role="system", content=f"失败：{reason}"))
        # 更新状态为 failed。
        self.status = TaskStatus.FAILED
