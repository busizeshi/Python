from __future__ import annotations

# 导入 pprint，方便更友好地打印字典结构。
from pprint import pprint
# 导入 sys/pathlib，用于脚本直接运行时自动设置导入路径。
import sys
from pathlib import Path

# 计算项目根目录。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 计算 src 目录。
SRC_DIR = PROJECT_ROOT / "src"
# 如果 src 还未加入路径，就插入。
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# 导入 A2A 编排器。
from multi_agent.a2a.orchestrator import A2AOrchestrator
# 导入 LangGraph 演示函数。
from multi_agent.langgraph_workflow import run_langgraph_demo


# 主程序入口。
if __name__ == "__main__":
    # 打印标题。
    print("=== LangGraph 中文演示 ===")
    # 执行一次数学任务演示。
    lg_result = run_langgraph_demo("计算 7 * (8 + 2)")
    # 打印结果。
    pprint(lg_result)

    # 打印分隔标题。
    print("\n=== A2A 中文演示 ===")
    # 创建编排器。
    orch = A2AOrchestrator()
    # 依次执行四种模式。
    for method in [
        orch.run_sequential,
        orch.run_parallel,
        orch.run_conditional,
        orch.run_pipeline,
    ]:
        # 执行当前模式。
        result = method("请设计工程级多智能体系统实施方案")
        # 打印模式名和结果。
        print(f"\n[{result['mode']}]\n{result['final']}")
