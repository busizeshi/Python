from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from config import CHAT_MODEL, DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL


class CopyWriterAgent:
    def __init__(self, model: str = CHAT_MODEL):
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.7,
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_BASE_URL,
        )
        self.template = PromptTemplate.from_template(
            "请为产品“{product}”写一句面向“{audience}”的广告文案。"
            "要求：只输出一句话，不超过15个字，不要解释。"
        )
        self.chain = self.template | self.llm | StrOutputParser()

    def run(self, product: str, audience: str) -> str:
        return self.chain.invoke({"product": product, "audience": audience}).strip()
