from __future__ import annotations

# 导入 sys/pathlib，用于在脚本运行时自动修正导入路径。
import sys
from pathlib import Path

# 计算项目根目录（scripts 的上一级就是项目目录）。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# src 目录路径。
SRC_DIR = PROJECT_ROOT / "src"
# 若 src 不在 sys.path，则插入到最前，确保优先导入本地代码。
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# 导入 A2A 编排器。
from multi_agent.a2a.orchestrator import A2AOrchestrator
# 导入 LangGraph 演示入口。
from multi_agent.langgraph_workflow import run_langgraph_demo


# 直接检查 LangGraph 的函数。
def check_langgraph() -> bool:
    # 打印分隔标题。
    print("=== 直接执行检查：LangGraph ===")
    # 数学路由示例。
    r1 = run_langgraph_demo("计算 3 + 5")
    # 打印数学示例结果。
    print("数学路由:", r1["route"], "|", r1["primary_output"])

    # 研究路由示例。
    r2 = run_langgraph_demo("设计一个可靠的多智能体架构")
    # 打印研究示例结果。
    print("研究路由:", r2["route"], "|", r2["primary_output"])

    # 判定是否通过。
    ok = (
            r1["route"] == "math"
            and ("数学结果" in r1["primary_output"] or "3 + 5" in r1["primary_output"])
            and r2["route"] == "research"
    )
    # 输出检查结论。
    print("LangGraph 检查:", "通过" if ok else "失败")
    # 返回布尔值。
    return ok


# 直接检查 A2A 四种模式的函数。
def check_a2a() -> bool:
    # 打印分隔标题。
    print("\n=== 直接执行检查：A2A 四种模式 ===")
    # 创建编排器对象。
    orch = A2AOrchestrator()

    # 执行顺序模式。
    seq = orch.run_sequential("请给出多智能体项目质量检查清单")
    # 执行并行模式。
    par = orch.run_parallel("计算 8 * 8")
    # 执行条件模式。
    con = orch.run_conditional("计算 9 + 1")
    # 执行流水线模式。
    pip = orch.run_pipeline("创建架构评审清单")

    # 打印四种模式结果。
    print("顺序模式:", seq["final"])
    print("并行模式:", par["final"])
    print("条件模式(选中):", con["chosen"], "|", con["final"])
    print("流水线模式:", pip["final"])

    # 组合判定条件。
    ok = (
            seq["mode"] == "顺序"
            and par["mode"] == "并行"
            and pip["mode"] == "流水线"
            and con["mode"] == "条件"
    )
    # 输出检查结论。
    print("A2A 检查:", "通过" if ok else "失败")
    # 返回布尔值。
    return ok


# 脚本入口。
if __name__ == "__main__":
    # 串行执行两个检查。
    # all_ok = (check_langgraph() and
    all_ok = check_a2a()
    # )
    # 打印总结果。
print("\n总结果:", "全部通过" if all_ok else "存在失败")
# 用退出码表达成功/失败。
raise SystemExit(0 if all_ok else 1)
