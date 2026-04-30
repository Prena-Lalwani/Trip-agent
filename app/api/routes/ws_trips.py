import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.security import decode_token
from app.db.database import AsyncSessionLocal
from app.models.trip import TripMember, TripMessage
from app.models.user import User
from app.services.trip_agent_service import maybe_respond
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/trips/{trip_id}/ws")
async def trip_room(trip_id: int, websocket: WebSocket, token: str):
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001)
        return

    user_id = int(payload["sub"])

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TripMember).where(
                TripMember.trip_id == trip_id,
                TripMember.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            await websocket.close(code=4003)
            return

        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        email = user_result.scalar_one().email

        # Send full history before joining live broadcast
        history_result = await db.execute(
            select(TripMessage)
            .where(TripMessage.trip_id == trip_id)
            .order_by(TripMessage.created_at)
        )
        history = history_result.scalars().all()

    await manager.connect(trip_id, websocket)

    for msg in history:
        await websocket.send_json({
            "type": "message",
            "user_id": msg.user_id,
            "user_email": msg.user_email,
            "is_agent": msg.is_agent,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat(),
        })

    try:
        while True:
            text = await websocket.receive_text()
            if not text.strip():
                continue

            now = datetime.now(timezone.utc)
            payload_msg = {
                "type": "message",
                "user_id": user_id,
                "user_email": email,
                "content": text,
                "timestamp": now.isoformat(),
            }

            async with AsyncSessionLocal() as db:
                db.add(TripMessage(
                    trip_id=trip_id,
                    user_id=user_id,
                    user_email=email,
                    content=text,
                    created_at=now,
                ))
                await db.commit()

            await manager.broadcast(trip_id, payload_msg)

            # Run agent in background — does not block the sender
            asyncio.create_task(maybe_respond(trip_id, text))

    except WebSocketDisconnect:
        manager.disconnect(trip_id, websocket)
