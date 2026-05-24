"""
run_service.py - FastAPI HTTP Service
"""
from fastapi.responses import JSONResponse
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agent import create_all_agents
import uvicorn

app = FastAPI(title="Multi-Agent Service")

# Initialize agents on startup
router, chat, meeting = create_all_agents(with_memory=True)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


from typing import Optional, List

class MeetingActionResponse(BaseModel):
    action: str
    owner: str
    deadline: Optional[str] = None

class ChatResponse(BaseModel):
    intent: str
    confidence: float
    response: str = ""
    meeting: Optional[dict] = None


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        decision = router.decide(req.message)

        if decision.intent == "meeting":
            result = meeting.summarize(req.message)
            return JSONResponse(content=json.loads(
                json.dumps({
                    "intent": decision.intent,
                    "confidence": decision.confidence,
                    "response": "",
                    "meeting": {
                        "title": result.title,
                        "date": result.date,
                        "attendees": result.attendees,
                        "summary": result.summary,
                        "decisions": result.decisions,
                        "action_items": [
                            {"action": a.action, "owner": a.owner, "deadline": a.deadline}
                            for a in result.action_items
                        ],
                        "notes": result.notes,
                    }
                }, ensure_ascii=False)
            ))
        else:
            response_text = chat.invoke(req.message)

        return ChatResponse(
            intent=decision.intent,
            confidence=decision.confidence,
            response=response_text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)