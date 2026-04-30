from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    thread_id: str
    reply: str
    input_tokens: int = 0
    output_tokens: int = 0


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    input_tokens: int
    output_tokens: int
    created_at: datetime


class ConversationResponse(BaseModel):
    id: int
    thread_id: str
    created_at: datetime
    messages: list[MessageResponse]


class TokenUsageResponse(BaseModel):
    conversation_id: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int