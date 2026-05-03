import os
import json
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from openai import OpenAI

# ==========================================
# 1. 基础配置
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SemanticRouting")


# ==========================================
# 2. Pydantic 模型：定义大模型必须返回的路由结果
# ==========================================
class LLMRouteDecision(BaseModel):
    """大模型直接输出的路由决策"""
    target_route: str = Field(
        description="选定的目标路由名称。必须是候选列表中的一个。"
    )
    confidence: float = Field(
        description="置信度 (0.0 - 1.0)。如果语义极其明确完全契合，给 0.9 以上；如果有歧义或模棱两可，给 0.6 以下。"
    )
    reason: str = Field(
        description="解释为什么选择这个路由，以及置信度打分的依据。"
    )


# ==========================================
# 3. 大模型接口抽象与通义千问 (Qwen) 实现 (复用基座)
# ==========================================
class LLMInterface(ABC):
    @abstractmethod
    def generate_structured(self, prompt: str, response_model: type[BaseModel]) -> BaseModel:
        pass


class QwenLLM(LLMInterface):
    def __init__(self, api_key: str = None, model_name: str = "qwen-plus"):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 API Key。请设置 DASHSCOPE_API_KEY 环境变量，或在初始化时传入。")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model_name = model_name

    def generate_structured(self, prompt: str, response_model: type[BaseModel]) -> BaseModel:
        schema = response_model.model_json_schema()
        system_prompt = f"""你是一个严格的数据格式化引擎。
请根据用户的指令，输出完全符合以下 JSON Schema 格式的数据。
JSON Schema:
{json.dumps(schema, ensure_ascii=False)}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            result_str = response.choices[0].message.content
            logger.debug(f"大模型原始返回:\n{result_str}")
            return response_model.model_validate_json(result_str)
        except Exception as e:
            logger.error(f"调用或解析时发生错误: {e}")
            raise


# ==========================================
# 4. 核心组件：语义路由器 (Semantic Router)
# ==========================================
class RouteDefinition(BaseModel):
    name: str
    description: str


class SemanticRouter:
    def __init__(self, llm: LLMInterface, fallback_route: str = "default_hybrid_retriever", threshold: float = 0.65):
        self.llm = llm
        self.routes: List[RouteDefinition] = []
        self.fallback_route = fallback_route
        self.threshold = threshold  # 置信度阈值，低于此值则触发 fallback

    def register_route(self, name: str, description: str):
        """注册可用的语义路由通道及其描述（原型）"""
        self.routes.append(RouteDefinition(name=name, description=description))

    def _build_prompt(self, query: str) -> str:
        # 将注册的路由列表拼接成 Prompt 供大模型参考
        routes_info = "\n".join([f"- {r.name}: {r.description}" for r in self.routes])

        prompt = f"""
你是一个智能检索系统的语义路由调度器（Router）。
你的任务是听懂用户的问题，并将其分配给最合适的专业检索器（Route）。

【可用路由列表及说明】
{routes_info}

【打分规则（极其重要）】
你需要输出目标路由（target_route）和置信度（confidence）。
- 0.9 - 1.0: 用户的意图与某个路由的描述【完美契合】。
- 0.7 - 0.8: 用户的意图【大致属于】某个路由，但不是特别典型。
- 0.0 - 0.6: 用户的意图【模糊不清、跨多个领域，或不属于上述任何路由】。此时请随意选一个最接近的，但必须打低分（<0.6）！

当前用户原始查询：{query}
"""
        return prompt

    def route(self, query: str) -> dict:
        logger.info(f"开始语义路由评估: [{query}]")
        prompt = self._build_prompt(query)

        # 1. 获取大模型的原始决策
        llm_decision: LLMRouteDecision = self.llm.generate_structured(prompt, LLMRouteDecision)

        # 2. 工程化校验：置信度回退机制 (Confidence Fallback)
        final_route = llm_decision.target_route
        is_fallback = False

        if llm_decision.confidence < self.threshold:
            logger.warning(
                f"大模型置信度过低 ({llm_decision.confidence} < {self.threshold})。 "
                f"触发回退机制！放弃模型推荐的 '{llm_decision.target_route}'，改为兜底路由 '{self.fallback_route}'"
            )
            final_route = self.fallback_route
            is_fallback = True

        return {
            "query": query,
            "final_route": final_route,
            "llm_suggested_route": llm_decision.target_route,
            "confidence": llm_decision.confidence,
            "is_fallback": is_fallback,
            "reason": llm_decision.reason
        }


# ==========================================
# 5. 运行与测试
# ==========================================
if __name__ == "__main__":
    try:
        qwen_llm = QwenLLM()
        router = SemanticRouter(llm=qwen_llm, fallback_route="default_hybrid_retriever", threshold=0.65)

        # --- 注册语义路由原型 (Route Prototypes) ---
        router.register_route(
            name="code_search_retriever",
            description="专门用于检索代码片段、API用法、报错排查、编程语言语法等技术问题。"
        )
        router.register_route(
            name="financial_report_retriever",
            description="专门用于检索公司的财务报表、营收数据、利润率、投资回报分析等商业财经数据。"
        )
        router.register_route(
            name="hr_policy_retriever",
            description="专门用于解答公司内部的人事制度、请假流程、报销规定、五险一金等员工福利问题。"
        )

        # --- 测试案例 ---
        test_queries = [
            "帮我查一下用 Python 连接 Redis 集群的示例代码",  # 预期: code_search_retriever (高置信度)
            "去年第四季度咱们公司的净利润是多少？",  # 预期: financial_report_retriever (高置信度)
            "我想查一下端午节放假怎么调休？",  # 预期: hr_policy_retriever (高置信度)
            "最近天气不错，推荐个适合旅游的城市吧"  # 预期: 置信度极低，触发 fallback 路由
        ]

        for i, query in enumerate(test_queries, 1):
            print("\n" + "=" * 50)
            print(f"--- 测试案例 {i} ---")

            decision = router.route(query)

            print(f"原问题   : {decision['query']}")
            if decision['is_fallback']:
                print(f"最终路由 : ⚠️ 降级到兜底路由 -> 【{decision['final_route']}】")
                print(f"模型建议 : {decision['llm_suggested_route']} (被否决，置信度仅为 {decision['confidence']})")
            else:
                print(f"最终路由 : 🎯 【{decision['final_route']}】")
                print(f"置信度   : {decision['confidence']}")

            print(f"大模型思考 : 📝 {decision['reason']}")
            print("=" * 50)

    except Exception as e:
        logger.error(f"运行失败: {e}")