from fastapi import FastAPI

from chains import build_router
from config import QDRANT_COLLECTION
from memory import append_turn, get_history
from router_schemas import ChatRequest, ChatResponse, FeedbackRequest
from tools import create_or_update_ticket

app = FastAPI(title="Helpdesk AI")
router = build_router(QDRANT_COLLECTION)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    append_turn(req.session_id, "user", req.query, {"user_id": req.user_id})
    routed = router.invoke({"query": req.query})

    if "create_or_update_ticket" in routed.get("actions", []):
        issue = routed["slots"].get("issue") or req.query
        priority = routed["slots"].get("priority", "normal")
        tk = create_or_update_ticket(
            req.user_id,
            issue,
            priority,
            extra={"history": get_history(req.session_id)},
        )
        msg = f"已为你创建工单 {tk['ticket_id']}（状态：{tk['status']}），我们会尽快处理。"
        append_turn(
            req.session_id,
            "assistant",
            msg,
            {"intent": routed["intent"], "ticket_id": tk["ticket_id"]},
        )
        return ChatResponse(
            intent=routed["intent"],
            answer=msg,
            ticket_id=tk["ticket_id"],
        )

    answer = routed.get("answer") or "抱歉，我未能理解你的问题，请补充更多信息。"
    append_turn(req.session_id, "assistant", answer, {"intent": routed["intent"]})
    return ChatResponse(intent=routed["intent"], answer=answer)


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    append_turn(req.session_id, "feedback", f"score={req.score}, comment={req.comment}")
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
