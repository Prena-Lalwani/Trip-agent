from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.conversation import Conversation, Message
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
    TokenUsageResponse,
)
from app.services.chat_service import get_token_usage, handle_chat, stream_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await handle_chat(
        user_id=int(current_user["sub"]),
        question=body.message,
        conversation_id=body.conversation_id,
        db=db,
    )


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE streaming endpoint. Events:
      - meta:     {"conversation_id": int, "thread_id": str}
      - progress: "Fetching weather data..." (node label)
      - token:    streamed text chunk
      - done:     signals stream end
    """
    return EventSourceResponse(
        stream_chat(
            user_id=int(current_user["sub"]),
            question=body.message,
            conversation_id=body.conversation_id,
            db=db,
        )
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == int(current_user["sub"])
        )
    )
    conversations = result.scalars().all()

    output = []
    for conv in conversations:
        msgs_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at)
        )
        messages = msgs_result.scalars().all()
        output.append(
            ConversationResponse(
                id=conv.id,
                thread_id=conv.thread_id,
                created_at=conv.created_at,
                messages=[
                    MessageResponse(
                        id=m.id,
                        role=m.role,
                        content=m.content,
                        input_tokens=m.input_tokens,
                        output_tokens=m.output_tokens,
                        created_at=m.created_at,
                    )
                    for m in messages
                ],
            )
        )
    return output


@router.get(
    "/conversations/{conversation_id}/tokens",
    response_model=TokenUsageResponse,
)
async def token_usage(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_token_usage(conversation_id, db)
