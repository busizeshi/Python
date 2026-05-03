from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from config import CHAT_MODEL, DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL


class ReviewerAgent:
    def __init__(self, model: str = CHAT_MODEL):
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.2,
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_BASE_URL,
        )
        self.template = PromptTemplate.from_template(
            "请优化这句广告文案，使其更适合年轻人：{text}\n"
            "要求：只输出最终一句话，不超过15个字，不要解释。"
        )
        self.chain = self.template | self.llm | StrOutputParser()

    def run(self, text: str) -> str:
        return self.chain.invoke({"text": text}).strip()
