import os
import json
import logging
from typing import Optional
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from openai import OpenAI

# ==========================================
# 1. 基础配置
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QueryHyDE")


# ==========================================
# 2. Pydantic 模型：定义大模型必须返回的数据结构
# ==========================================
class HyDEResult(BaseModel):
    """HyDE 假设性文档生成的结果模型"""
    is_suitable_for_hyde: bool = Field(
        description="是否适合使用 HyDE。如果问题涉及高度精确的事实（如特定错误码、特定账单数据），存在极高幻觉风险，则为False。"
    )
    hypothetical_document: Optional[str] = Field(
        description="生成的假设性文档片段。如果不适合使用HyDE，则此字段为空(null)。不要带有Markdown格式，纯文本即可。"
    )
    reason: str = Field(
        description="解释为什么适合/不适合生成假设性文档。"
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
# 4. 核心组件：HyDE 假设性文档生成器 (Query HyDE Generator)
# ==========================================
class QueryHyDEGenerator:
    def __init__(self, llm: LLMInterface):
        self.llm = llm

    def _build_prompt(self, original_query: str) -> str:
        """
        工程级 Prompt 核心注意点：
        1. 赋予大模型“专家角色”，让它用专业的术语和口吻回答。
        2. 强调“包含核心术语”，因为 HyDE 的本质是补充语义特征词。
        3. 必须设置“幻觉熔断机制”（Fact-check protection）。
        """
        prompt = f"""
你是一个资深的领域专家。请针对用户的简短查询，编写一段【假设性文档片段】。
这段片段不需要完全真实（因为最终用于向量检索），但它必须看起来像是一篇讨论该主题的专业文档，并且要包含大量相关的【专业术语】和【特征词】。

【核心规则】
1. 文档长度适中（50-150字），不要长篇大论。
2. 以陈述句为主，语气专业，像是在维基百科或技术博客中摘录的片段。
3. 高风险事实保护（关键）：如果用户的查询是在询问极其精确的硬事实（如：订单 10245 的状态、某个非常具体的错误代码 0x80070422 的直接原因、某人的确切家庭住址），请将 is_suitable_for_hyde 设置为 false！因为胡乱编造这些精确事实的假文档，会导致后续检索出完全错误的资料。只有对于概念性、原理性、广泛性的问题，才生成文档。

【示例】
[示例 1 - 适合 HyDE：概念与原理]
用户：什么是大模型中的 RAG？
预期输出：
is_suitable_for_hyde: true
hypothetical_document: "RAG（检索增强生成）是一种结合了信息检索和大规模语言模型（LLM）架构的技术。它通过在外挂知识库（如向量数据库）中实时检索与用户查询相关的上下文文档，并将其与原始问题结合后输入给LLM，从而有效缓解大模型的幻觉问题，提升回答的准确性和事实性。"

[示例 2 - 适合 HyDE：短小宽泛的词]
用户：GPU 显存带宽
预期输出：
is_suitable_for_hyde: true
hypothetical_document: "GPU显存带宽是指显卡内存与GPU核心之间的数据传输速率，通常由显存位宽和显存频率共同决定。高显存带宽对于处理深度学习训练、大规模并行计算以及高分辨率纹理渲染至关重要，能有效避免数据传输瓶颈引发的计算等待。"

[示例 3 - 不适合 HyDE：高风险精确事实]
用户：客户张三的报销单 BXD-2023-001 审批卡在哪一步了？
预期输出：
is_suitable_for_hyde: false
hypothetical_document: null
（解释：这是私有精确数据，模型生成的假审批流程会严重干扰后续检索）

当前用户原始查询：{original_query}
"""
        return prompt

    def generate(self, query: str) -> HyDEResult:
        logger.info(f"接收到查询，准备生成 HyDE 假设文档: [{query}]")
        prompt = self._build_prompt(query)

        result: HyDEResult = self.llm.generate_structured(prompt, HyDEResult)
        return result


# ==========================================
# 5. 运行与测试
# ==========================================
if __name__ == "__main__":
    try:
        # 初始化千问客户端（请确保环境变量 DASHSCOPE_API_KEY 已配置）
        qwen_llm = QwenLLM()
        hyde_generator = QueryHyDEGenerator(qwen_llm)

        test_queries = [
            "什么是向量数据库？",  # 案例1：非常适合，补充特征词
            "帮我解释一下 TCP 三次握手过程",  # 案例2：非常适合，补充技术细节
            "昨天服务器报 Error Code 502 Bad Gateway 是哪台机器？"  # 案例3：事实敏感，禁止 HyDE 捏造
        ]

        for i, query in enumerate(test_queries, 1):
            print("\n" + "=" * 50)
            print(f"--- 测试案例 {i} ---")
            print(f"原问题   : {query}")

            res = hyde_generator.generate(query)

            print(f"适用HyDE : {'✅ 是 (True)' if res.is_suitable_for_hyde else '❌ 否 (False)'}")
            if res.is_suitable_for_hyde:
                print(f"假设文档 :\n{res.hypothetical_document}")
            print(f"执行原因 : 📝 {res.reason}")
            print("=" * 50)

    except Exception as e:
        logger.error(f"运行失败: {e}")