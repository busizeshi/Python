import os
import json
import logging
from typing import List
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

# 如果没有安装，请先执行：pip install openai pydantic
from openai import OpenAI

# ==========================================
# 1. 基础配置
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QueryRewrite")


# ==========================================
# 2. Pydantic 模型：定义大模型必须返回的数据结构
# ==========================================
class RewriteResult(BaseModel):
    """查询重写的结果模型"""
    is_modified: bool = Field(description="是否对原查询进行了修改（如果原查询已经很完美，为False）")
    rewritten_query: str = Field(description="重写后的检索查询，去除了口语化，补齐了信息")
    keywords: List[str] = Field(description="提取的核心关键词列表，用于 BM25 等传统词汇检索")
    reason: str = Field(description="解释为什么这样重写（便于开发调试查日志）")


# ==========================================
# 3. 大模型接口抽象与通义千问 (Qwen) 实现
# ==========================================
class LLMInterface(ABC):
    @abstractmethod
    def generate_structured(self, prompt: str, response_model: type[BaseModel]) -> BaseModel:
        pass


class QwenLLM(LLMInterface):
    """
    基于阿里云 DashScope (通义千问) 的 LLM 实现。
    使用 OpenAI 兼容的 API 模式，天然支持结构化 JSON 输出。
    """

    def __init__(self, api_key: str = None, model_name: str = "qwen-plus"):
        # 优先使用传入的 api_key，否则从环境变量读取
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 API Key。请设置 DASHSCOPE_API_KEY 环境变量，或在初始化时传入。")

        # 初始化 OpenAI 客户端，指向阿里云千问的兼容地址
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model_name = model_name

    def generate_structured(self, prompt: str, response_model: type[BaseModel]) -> BaseModel:
        # 1. 提取 Pydantic 模型的 JSON Schema，用来指导大模型输出
        schema = response_model.model_json_schema()

        system_prompt = f"""你是一个严格的数据格式化引擎。
请根据用户的指令，输出完全符合以下 JSON Schema 格式的数据。
除了合法的 JSON 字符串之外，不要输出任何其他的解释文本（不要使用 Markdown 标记，不要回答"好的"）。

JSON Schema:
{json.dumps(schema, ensure_ascii=False)}"""

        try:
            # 2. 调用千问 API，强制要求输出 json_object 格式
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result_str = response.choices[0].message.content
            logger.debug(f"千问大模型原始返回:\n{result_str}")

            # 3. 使用 Pydantic 将 JSON 字符串校验并转化为 Python 对象
            return response_model.model_validate_json(result_str)

        except Exception as e:
            logger.error(f"调用通义千问或解析数据时发生错误: {e}")
            raise


# ==========================================
# 4. 核心组件：查询重写器 (Query Rewriter)
# ==========================================
class QueryRewriter:
    def __init__(self, llm: LLMInterface):
        self.llm = llm

    def _build_prompt(self, original_query: str) -> str:
        """
        工程级 Prompt 设计核心：
        包含了角色设定、任务目标、严格规则以及 Few-Shot (少样本示例)
        """
        prompt = f"""
你是一个资深的搜索引擎算法专家。
你的任务是将用户的口语化查询转化为结构化、精准、对检索系统（向量库+BM25词汇引擎）极其友好的查询。

【规则】
1. 剔除无用的语气词（如“帮我查一下”、“那个”、“请问”等）。
2. 如果存在指代不清（如“那个很火的”），请根据当前行业常识补齐具体的实体。
3. 如果原查询已经非常清晰专业，请不要过度修改它（令 is_modified = false）。
4. 提取核心的 keywords，不仅包含原词，还可以包含极其常见的英文/中文简写缩写。

【示例】
用户：帮我对比下最近那个很火的国产大模型和GPT-4
输出思考（不需要在最终JSON中包含，仅作为参考思路）：用户提到的很火的国产可能是DeepSeek/千问/Kimi等，需要补齐。
预期输出逻辑应该对应：DeepSeek/通义千问等国产大模型与 GPT-4 的能力全方位对比评测

用户原始查询：{original_query}
"""
        return prompt

    def rewrite(self, query: str) -> RewriteResult:
        logger.info(f"接收到原始查询: [{query}]")

        # 1. 构建带有业务规则的 Prompt
        prompt = self._build_prompt(query)

        # 2. 调用大模型，强制输出结构化数据
        logger.info("正在调用千问模型进行分析与重写...")
        result: RewriteResult = self.llm.generate_structured(prompt, RewriteResult)

        return result


# ==========================================
# 5. 运行与测试
# ==========================================
if __name__ == "__main__":
    # 注意：请确保你在环境变量中设置了 DASHSCOPE_API_KEY
    # 或者在这里直接传入：QwenLLM(api_key="sk-xxxxxxxxxxxxx")
    try:
        qwen_llm = QwenLLM()
        rewriter = QueryRewriter(qwen_llm)

        # 测试案例 1：极其口语化且模糊的问题
        query1 = "最近那个很火的向量库哪个好，帮我查查"
        res1 = rewriter.rewrite(query1)

        print("\n" + "=" * 40)
        print("--- 测试案例 1 ---")
        print(f"原问题   : {query1}")
        print(f"重写后   : {res1.rewritten_query}")
        print(f"关键词   : {res1.keywords}")
        print(f"修改原因 : {res1.reason}")
        print("=" * 40 + "\n")

        # 测试案例 2：本身已经很精准的问题
        query2 = "Python 字典的 keys() 和 values() 方法的时间复杂度对比"
        res2 = rewriter.rewrite(query2)

        print("=" * 40)
        print("--- 测试案例 2 ---")
        print(f"原问题   : {query2}")
        print(f"是否修改 : {res2.is_modified}")
        print(f"重写后   : {res2.rewritten_query}")
        print(f"关键词   : {res2.keywords}")
        print(f"修改原因 : {res2.reason}")
        print("=" * 40 + "\n")

    except Exception as e:
        logger.error(f"运行失败: {e}")