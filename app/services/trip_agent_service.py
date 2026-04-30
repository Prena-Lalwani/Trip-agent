from datetime import datetime, timezone

from langchain_core.messages import HumanMessage
from sqlalchemy import select

from app.agents.graph import travel_graph
from app.agents.trip_gatekeeper import check as gatekeeper_check
from app.db.database import AsyncSessionLocal
from app.models.trip import TripMessage
from app.websocket.manager import manager

AGENT_EMAIL = "Travel Agent"


def _build_inputs(question: str, chat_context: str) -> dict:
    full_query = (
        f"This is a group trip planning chat. "
        f"Here is the recent conversation:\n{chat_context}"
        f"\n\nQuestion to answer: {question}"
    )
    return {
        "messages": [HumanMessage(content=full_query)],
        "user_query": full_query,
        "weather_query": "",
        "info_query": "",
        "planner_query": "",
        "weather_data": "",
        "destination_info": "",
        "travel_plan": "",
        "final_response": "",
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }


async def maybe_respond(trip_id: int, new_message: str) -> None:
    """Run gatekeeper; if approved, invoke LangGraph and broadcast reply."""
    # Fetch last 50 messages — used for both gatekeeper and agent context
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TripMessage)
            .where(TripMessage.trip_id == trip_id)
            .order_by(TripMessage.created_at.desc())
            .limit(50)
        )
        recent = list(reversed(result.scalars().all()))

    msg_dicts = [
        {
            "user_email": m.user_email,
            "content": m.content,
            "is_agent": m.is_agent,
        }
        for m in recent
    ]

    should_respond, question = await gatekeeper_check(msg_dicts, new_message)
    if not should_respond or not question:
        return

    chat_context = "\n".join(
        f"[Travel Agent]: {m['content']}"
        if m["is_agent"]
        else f"{m['user_email']}: {m['content']}"
        for m in msg_dicts
    )

    config = {"configurable": {"thread_id": f"trip-{trip_id}"}}
    result = await travel_graph.ainvoke(
        _build_inputs(question, chat_context), config=config
    )
    reply = result.get("final_response", "").strip()
    if not reply:
        return

    now = datetime.now(timezone.utc)
    payload = {
        "type": "message",
        "user_id": None,
        "user_email": AGENT_EMAIL,
        "is_agent": True,
        "content": reply,
        "timestamp": now.isoformat(),
    }

    async with AsyncSessionLocal() as db:
        db.add(TripMessage(
            trip_id=trip_id,
            user_id=None,
            user_email=AGENT_EMAIL,
            content=reply,
            is_agent=True,
            created_at=now,
        ))
        await db.commit()

    await manager.broadcast(trip_id, payload)
