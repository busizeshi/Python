import os
import json
import logging
from typing import List
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from openai import OpenAI

# ==========================================
# 1. 基础配置
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QueryDecompose")


# ==========================================
# 2. Pydantic 模型：定义大模型必须返回的数据结构
# ==========================================
class DecomposeResult(BaseModel):
    """查询分解的结果模型"""
    is_complex: bool = Field(description="是否属于包含多个意图的复杂查询。如果是单一简单查询，则为False。")
    sub_queries: List[str] = Field(
        description="拆解出的独立子查询列表。如果不是复杂查询，这里只放原查询（或稍微润色后的原查询）。")
    reason: str = Field(description="解释为什么这样拆解，或者为什么不拆解（便于排查降级/噪声问题）。")


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
# 4. 核心组件：查询分解器 (Query Decomposer)
# ==========================================
class QueryDecomposer:
    def __init__(self, llm: LLMInterface):
        self.llm = llm

    def _build_prompt(self, original_query: str) -> str:
        """
        工程级 Prompt 核心注意点：
        1. 必须强调“子查询需包含完整上下文”（比如不能拆出“它的价格是多少”，必须是“A产品的价格是多少”）。
        2. 必须强调“适度拆分”，防止把一句话拆成十几个字导致召回大量垃圾噪声。
        """
        prompt = f"""
你是一个资深的 RAG（检索增强生成）系统算法专家。
你的任务是将用户的原始查询（Query）判断并分解为多个可以【独立并行检索】的子查询（Sub-queries）。

【核心规则】
1. 识别是否复杂：如果原查询只有一个明确目标，请设置 is_complex=false，并在 sub_queries 中仅保留原意。
2. 独立完整性（关键）：拆解出的每一个子查询，必须能够独立脱离上下文进行检索。决不能包含代词（如“它”、“这个”），必须补全实体名称。
3. 颗粒度适中：不要拆得太碎！通常 2-4 个子查询为宜。避免产生过度发散的无关查询。

【示例】
[示例 1 - 复杂对比场景]
用户：帮我比较下 LangChain 和 LlamaIndex，顺便说说如果是新手做个简单的知识库该用哪个？
输出思考：包含 A的特点、B的特点、对比、以及针对新手的选型建议。
预期结构化输出：
is_complex: true
sub_queries: ["LangChain 的核心功能与优缺点", "LlamaIndex 的核心功能与优缺点", "LangChain 与 LlamaIndex 的全方位对比", "针对新手的简单知识库构建框架选型建议"]

[示例 2 - 简单单一场景]
用户：Qdrant 怎么设置索引的阈值参数？
输出思考：目标极其明确，就是查一个特定的操作参数。
预期结构化输出：
is_complex: false
sub_queries: ["Qdrant 设置索引阈值参数的配置方法"]

当前用户原始查询：{original_query}
"""
        return prompt

    def decompose(self, query: str) -> DecomposeResult:
        logger.info(f"接收到待分解查询: [{query}]")
        prompt = self._build_prompt(query)

        logger.info("正在分析查询复杂度并尝试分解...")
        result: DecomposeResult = self.llm.generate_structured(prompt, DecomposeResult)

        return result


# ==========================================
# 5. 运行与测试
# ==========================================
if __name__ == "__main__":
    try:
        # 初始化千问客户端（请确保环境变量 DASHSCOPE_API_KEY 已配置）
        qwen_llm = QwenLLM()
        decomposer = QueryDecomposer(qwen_llm)

        # 测试案例 1：典型的“对比 + 建议”复合查询
        query1 = "DeepSeek和通义千问哪个写代码强？另外它们分别支持多大的上下文？"
        res1 = decomposer.decompose(query1)

        print("\n" + "=" * 50)
        print("--- 测试案例 1：复杂复合查询 ---")
        print(f"原问题   : {query1}")
        print(f"是否复杂 : {res1.is_complex}")
        print(f"拆解结果 :")
        for i, sq in enumerate(res1.sub_queries, 1):
            print(f"  {i}. {sq}")
        print(f"执行原因 : {res1.reason}")
        print("=" * 50 + "\n")

        # 测试案例 2：不需要拆解的简单查询（防误操作测试）
        query2 = "如何解决 Python 的 ModuleNotFoundError 报错？"
        res2 = decomposer.decompose(query2)

        print("--- 测试案例 2：简单单一查询 ---")
        print(f"原问题   : {query2}")
        print(f"是否复杂 : {res2.is_complex}")
        print(f"拆解结果 : {res2.sub_queries}")
        print(f"执行原因 : {res2.reason}")
        print("=" * 50 + "\n")

    except Exception as e:
        logger.error(f"运行失败: {e}")