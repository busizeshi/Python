from __future__ import annotations

# 导入 TypedDict 用来定义 LangGraph 状态结构。
from typing import TypedDict

# 导入 LangGraph 的起止常量和图构建器。
from langgraph.graph import END, START, StateGraph

# 导入我们封装的 Agent 构建函数。
from .agents import build_agents


# 这是图中流转的状态对象定义。
class WorkflowState(TypedDict):
    # 原始输入问题。
    query: str
    # 路由结果：math 或 research。
    route: str
    # 主处理节点输出。
    primary_output: str
    # 主处理节点置信度。
    confidence: float
    # 评审节点输出。
    critic_feedback: str
    # 合并后的最终答案。
    final_answer: str


# 初始化 Agent。
supervisor, math_agent, research_agent, critic_agent = build_agents()


# Supervisor 节点：只负责决定路由。
def supervisor_node(state: WorkflowState) -> WorkflowState:
    # 取 query 并做路由判断。
    route = supervisor.route(state["query"])
    # 返回更新后的新状态。
    return {**state, "route": route}


# Math 节点：处理数学任务。
def math_node(state: WorkflowState) -> WorkflowState:
    # 调用数学 Agent。
    result = math_agent.run(state["query"])
    # 回写输出和置信度。
    return {
        **state,
        "primary_output": result.output,
        "confidence": result.confidence,
    }


# Research 节点：处理研究任务。
def research_node(state: WorkflowState) -> WorkflowState:
    # 调用研究 Agent。
    result = research_agent.run(state["query"])
    # 回写输出和置信度。
    return {
        **state,
        "primary_output": result.output,
        "confidence": result.confidence,
    }


# Critic 节点：对主输出做评审。
def critic_node(state: WorkflowState) -> WorkflowState:
    # 传入 primary_output 做质量评审。
    result = critic_agent.run(state["primary_output"])
    # 回写评审结论。
    return {**state, "critic_feedback": result.output}


# Merge 节点：把主输出、置信度、评审意见合并成最终文本。
def merge_node(state: WorkflowState) -> WorkflowState:
    # 构造最终答案。
    final = (
        f"主结果：{state['primary_output']}\n"
        f"置信度：{state['confidence']:.2f}\n"
        f"评审：{state['critic_feedback']}"
    )
    # 回写 final_answer。
    return {**state, "final_answer": final}


# 路由函数：LangGraph 会根据返回值走不同边。
def router(state: WorkflowState) -> str:
    # 直接返回 route 字段。
    return state["route"]


# 构建并编译状态图。
def build_graph():
    # 创建 StateGraph，绑定状态类型。
    graph = StateGraph(WorkflowState)
    # 注册 supervisor 节点。
    graph.add_node("supervisor", supervisor_node)
    # 注册 math 节点。
    graph.add_node("math", math_node)
    # 注册 research 节点。
    graph.add_node("research", research_node)
    # 注册 critic 节点。
    graph.add_node("critic", critic_node)
    # 注册 merge 节点。
    graph.add_node("merge", merge_node)

    # 从 START 进入 supervisor。
    graph.add_edge(START, "supervisor")
    # supervisor 条件分支到 math 或 research。
    graph.add_conditional_edges(
        "supervisor",
        router,
        path_map={"math": "math", "research": "research"},
    )
    # math 完成后进入 critic。
    graph.add_edge("math", "critic")
    # research 完成后进入 critic。
    graph.add_edge("research", "critic")
    # critic 完成后进入 merge。
    graph.add_edge("critic", "merge")
    # merge 完成后到 END。
    graph.add_edge("merge", END)
    # 编译图并返回可调用对象。
    return graph.compile()


# 对外演示函数：给定 query，返回执行后的最终状态。
def run_langgraph_demo(query: str) -> WorkflowState:
    # 创建可执行图实例。
    app = build_graph()
    # 准备初始状态。
    initial: WorkflowState = {
        "query": query,
        "route": "",
        "primary_output": "",
        "confidence": 0.0,
        "critic_feedback": "",
        "final_answer": "",
    }
    # 调用图执行并返回最终状态。
    return app.invoke(initial)
