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
logger = logging.getLogger("QueryExpand")


# ==========================================
# 2. Pydantic 模型：定义大模型必须返回的数据结构
# ==========================================
class ExpandResult(BaseModel):
    """查询扩展的结果模型"""
    needs_expansion: bool = Field(
        description="是否需要扩展。如果是极其精确的实体（如特定错误码、特定人名、UUID），不需要扩展则为False。"
    )
    expanded_terms: List[str] = Field(
        description="扩展出的同义词、缩写、中英文翻译或密切相关的术语列表。如果没有则为空列表。"
    )
    reason: str = Field(
        description="解释扩展了哪些维度的词，或者为什么认为不需要扩展。"
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
# 4. 核心组件：查询扩展器 (Query Expander)
# ==========================================
class QueryExpander:
    def __init__(self, llm: LLMInterface):
        self.llm = llm

    def _build_prompt(self, original_query: str) -> str:
        """
        工程级 Prompt 核心注意点：
        1. 明确扩展的维度：同义词、缩写（如 大语言模型 -> LLM）、中英互译。
        2. 强约束边界：绝不能跑题！不能凭空捏造无关概念。
        3. 熔断机制：针对精准检索词（如 UUID、特定错误码），直接熔断，禁止扩展。
        """
        prompt = f"""
你是一个资深的搜索引擎算法专家。
你的任务是为用户的原始查询（Query）提供【查询扩展】，以提升召回率（Recall），解决词汇不匹配的问题。

【扩展规则】
1. 扩展维度：请提取原查询中的核心概念，并补充其【同义词】、【常见缩写】、【中英文翻译】或【专业术语变体】。
2. 宁缺毋滥：扩展词必须与原意高度相关，绝不能偏题或发散到无关领域。控制在 3-5 个词以内。
3. 精确词保护（关键）：如果用户查询的是非常精确的实体（例如：明确的错误码如"0x80070005"、具体的 UUID、特定的人名、专有版本号等），过度扩展会引入严重的噪声。此时请设置 needs_expansion=false，并返回空列表。

【示例】
[示例 1 - 需要扩展]
用户：GPU 显存带宽
预期输出：needs_expansion=true, expanded_terms=["memory bandwidth", "显存吞吐", "VRAM带宽", "显存频率"]

[示例 2 - 精确匹配，禁止扩展]
用户：安装失败报错 0x80070422 怎么解决
预期输出：needs_expansion=false, expanded_terms=[] （解释：包含明确的十六进制错误码，强行扩展如"系统错误"会导致召回大量不相关文档）

[示例 3 - 缩写与翻译]
用户：大模型 幻觉
预期输出：needs_expansion=true, expanded_terms=["LLM", "Large Language Model", "Hallucination", "事实一致性"]

当前用户原始查询：{original_query}
"""
        return prompt

    def expand(self, query: str) -> ExpandResult:
        logger.info(f"接收到查询，准备进行扩展分析: [{query}]")
        prompt = self._build_prompt(query)

        result: ExpandResult = self.llm.generate_structured(prompt, ExpandResult)
        return result


# ==========================================
# 5. 运行与测试
# ==========================================
if __name__ == "__main__":
    try:
        # 初始化千问客户端（请确保环境变量 DASHSCOPE_API_KEY 已配置）
        qwen_llm = QwenLLM()
        expander = QueryExpander(qwen_llm)

        test_queries = [
            "K8s 弹性伸缩配置",  # 案例1：包含缩写，需要扩展中英文和全称
            "大模型 RAG 架构的缺点",  # 案例2：包含行业黑话，需要扩展
            "用户张三的订单号 E202310249981 状态"  # 案例3：极其精确的实体，测试防发散机制
        ]

        for i, query in enumerate(test_queries, 1):
            print("\n" + "=" * 50)
            print(f"--- 测试案例 {i} ---")
            print(f"原问题   : {query}")

            res = expander.expand(query)

            print(f"是否扩展 : {'✅ 是 (True)' if res.needs_expansion else '❌ 否 (False)'}")
            if res.needs_expansion:
                print(f"扩展词汇 : {', '.join(res.expanded_terms)}")
            print(f"执行原因 : 📝 {res.reason}")
            print("=" * 50)

    except Exception as e:
        logger.error(f"运行失败: {e}")