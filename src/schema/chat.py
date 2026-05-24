from typing import Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """
    Chat request body

    Attributes:
        message: The message content sent by the user
        session_id: Session identifier used to link the same conversation
    """
    message: str = Field(..., min_length=1, max_length=8000, description="The user message")
    session_id: Optional[str] = Field(default=None, description="The session identifier")

class ChatResponse(BaseModel):
    """
    Chat response body

    Attributes:
        reply: The content replied by the AI
        session_id: Session identifier
        intent: The recognized user intent
    """
    reply: str = Field(..., description="The reply content")
    session_id: Optional[str] = Field(default=None, description="The session identifier")
    intent: Optional[str] = Field(default=None, description="The recognized intent")