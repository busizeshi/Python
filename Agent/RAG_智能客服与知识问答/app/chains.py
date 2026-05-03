from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_qdrant import QdrantVectorStore

from config import (
    CHAT_MODEL,
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    EMBEDDING_MODEL,
    QDRANT_API_KEY,
    QDRANT_URL,
)
from embeddings import DashScopeEmbeddings

INTENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是企业客服意图路由器。请根据用户问题判断意图和槽位。"
            "意图只能从 {labels} 中选择，并严格输出 JSON，格式为"
            "{{\"intent\":\"FAQ\",\"slots\":{{}}}}。",
        ),
        ("human", "{query}"),
    ]
)


def build_intent_chain(labels=("FAQ", "TICKET", "COMPLAINT", "ESCALATION")):
    llm = ChatOpenAI(
        model=CHAT_MODEL,
        temperature=0,
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
    )
    chain = INTENT_PROMPT | llm | StrOutputParser()
    return chain, labels


def build_rag_chain(collection_name: str):
    embeddings = DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
    )
    retriever = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=collection_name,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    ).as_retriever(search_kwargs={"k": 4})

    rag_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是企业 FAQ 助手。请基于检索结果作答，并在答案中体现依据。"
                "如果检索不到有效信息，请明确说明并建议转工单。",
            ),
            ("human", "问题：{query}\n\n检索结果：\n{contexts}"),
        ]
    )

    def fetch_ctx(x: Dict[str, Any]):
        docs = retriever.invoke(x["query"])
        cites = "\n\n".join(
            [
                f"[{i + 1}] {d.page_content[:300]} "
                f"(source={d.metadata.get('source')}, chunk={d.metadata.get('chunk_id')})"
                for i, d in enumerate(docs)
            ]
        )
        return {"query": x["query"], "contexts": cites}

    llm = ChatOpenAI(
        model=CHAT_MODEL,
        temperature=0,
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
    )
    chain = RunnablePassthrough() | RunnableLambda(fetch_ctx) | rag_prompt | llm | StrOutputParser()
    return chain


def build_router(collection_name: str):
    intent_chain, labels = build_intent_chain(
        labels=("FAQ", "TICKET", "COMPLAINT", "ESCALATION")
    )
    rag_chain = build_rag_chain(collection_name)

    def route(payload):
        import json

        intent_json = intent_chain.invoke(
            {"query": payload["query"], "labels": list(labels)}
        )
        try:
            info = json.loads(intent_json)
            intent = info.get("intent", "FAQ")
            slots = info.get("slots", {})
        except Exception:
            intent, slots = "FAQ", {}

        if intent == "FAQ":
            answer = rag_chain.invoke({"query": payload["query"]})
            return {"intent": intent, "slots": slots, "answer": answer, "actions": []}
        if intent in ("TICKET", "COMPLAINT", "ESCALATION"):
            return {
                "intent": intent,
                "slots": slots,
                "answer": None,
                "actions": ["create_or_update_ticket"],
            }
        return {
            "intent": "FAQ",
            "slots": slots,
            "answer": rag_chain.invoke({"query": payload["query"]}),
            "actions": [],
        }

    return RunnableLambda(route)
