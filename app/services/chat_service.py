import uuid
from typing import AsyncGenerator

from langchain_core.messages import AIMessageChunk, HumanMessage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import travel_graph
from app.models.conversation import Conversation, Message
from app.models.user import User

_NODE_LABELS = {
    "router":        "Thinking...",
    "extractor":     "Extracting travel details...",
    "weather_agent": "Fetching weather data...",
    "info_agent":    "Researching destination...",
    "planner_agent": "Creating your travel plan...",
    "aggregator":    "Formatting response...",
}


async def _get_or_create_conversation(
    user_id: int, conversation_id: int | None, db: AsyncSession
) -> Conversation:
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

    conv = Conversation(user_id=user_id, thread_id=str(uuid.uuid4()))
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


def _build_inputs(user_query: str) -> dict:
    return {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "weather_query": "",
        "info_query": "",
        "planner_query": "",
        "weather_data": "",
        "destination_info": "",
        "travel_plan": "",
        "final_response": "",
        # Reset token counters each turn (operator.add adds 0 = no carry-over)
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }


async def _save_turn(
    db: AsyncSession,
    conv: Conversation,
    user_id: int,
    question: str,
    reply: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
) -> None:
    user = await db.get(User, user_id)
    if user:
        user.total_consumed_tokens += total_tokens

    db.add(Message(conversation_id=conv.id, role="user", content=question))
    db.add(Message(
        conversation_id=conv.id,
        role="assistant",
        content=reply,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    ))
    await db.commit()


async def handle_chat(
    user_id: int,
    question: str,
    conversation_id: int | None,
    db: AsyncSession,
) -> dict:
    conv = await _get_or_create_conversation(user_id, conversation_id, db)
    config = {"configurable": {"thread_id": conv.thread_id}}

    result = await travel_graph.ainvoke(_build_inputs(question), config=config)
    reply = result.get("final_response", "")
    input_tokens = result.get("input_tokens", 0)
    output_tokens = result.get("output_tokens", 0)
    total_tokens = result.get("total_tokens", 0)

    await _save_turn(
        db, conv, user_id, question, reply,
        input_tokens, output_tokens, total_tokens,
    )

    return {
        "conversation_id": conv.id,
        "thread_id": conv.thread_id,
        "reply": reply,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


async def stream_chat(
    user_id: int,
    question: str,
    conversation_id: int | None,
    db: AsyncSession,
) -> AsyncGenerator[dict, None]:
    conv = await _get_or_create_conversation(user_id, conversation_id, db)
    config = {"configurable": {"thread_id": conv.thread_id}}

    yield {
        "event": "meta",
        "data": (
            f'{{"conversation_id":{conv.id},'
            f'"thread_id":"{conv.thread_id}"}}'
        ),
    }

    seen_nodes: set[str] = set()
    full_reply: list[str] = []

    async for chunk, metadata in travel_graph.astream(
        _build_inputs(question), config=config, stream_mode="messages"
    ):
        node = metadata.get("langgraph_node", "")

        if node in _NODE_LABELS and node not in seen_nodes:
            seen_nodes.add(node)
            yield {"event": "progress", "data": _NODE_LABELS[node]}

        if node in ("aggregator", "chat"):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                full_reply.append(chunk.content)
                yield {"event": "token", "data": chunk.content}

    # Read final token counts from graph state
    final_state = await travel_graph.aget_state(config)
    vals = final_state.values if final_state else {}
    input_tokens = vals.get("input_tokens", 0)
    output_tokens = vals.get("output_tokens", 0)
    total_tokens = vals.get("total_tokens", 0)

    reply = "".join(full_reply)
    await _save_turn(
        db, conv, user_id, question, reply,
        input_tokens, output_tokens, total_tokens,
    )

    yield {
        "event": "done",
        "data": (
            f'{{"input_tokens":{input_tokens},'
            f'"output_tokens":{output_tokens},'
            f'"total_tokens":{total_tokens}}}'
        ),
    }



async def get_token_usage(conversation_id: int, db: AsyncSession) -> dict:
    result = await db.execute(
        select(
            func.sum(Message.input_tokens).label("total_input"),
            func.sum(Message.output_tokens).label("total_output"),
        ).where(Message.conversation_id == conversation_id)
    )
    row = result.one()
    total_in = row.total_input or 0
    total_out = row.total_output or 0
    return {
        "conversation_id": conversation_id,
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "total_tokens": total_in + total_out,
    }