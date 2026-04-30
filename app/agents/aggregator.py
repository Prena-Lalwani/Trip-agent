from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import TravelState
from app.core.config import settings

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.google_api_key,
    temperature=0.3,
)

_system_prompt = Path("app/prompts/aggregator.txt").read_text(encoding="utf-8")


async def aggregator_node(state: TravelState) -> dict:
    weather = state.get("weather_data", "").strip()
    info = state.get("destination_info", "").strip()
    plan = state.get("travel_plan", "").strip()

    parts = []
    if plan:
        parts.append(f"Travel Plan:\n{plan}")
    if weather:
        parts.append(f"Weather Information:\n{weather}")
    if info:
        parts.append(f"Destination Research:\n{info}")

    content = (
        "\n\n---\n\n".join(parts)
        if parts
        else "No travel data was gathered. Ask the user to clarify."
    )

    messages = [
        SystemMessage(content=_system_prompt),
        HumanMessage(content=content),
    ]
    response = await _llm.ainvoke(messages)
    usage = response.usage_metadata or {}
    i = usage.get("input_tokens", 0)
    o = usage.get("output_tokens", 0)
    return {
        "final_response": response.content,
        "messages": [AIMessage(content=response.content)],
        "input_tokens": i,
        "output_tokens": o,
        "total_tokens": usage.get("total_tokens", i + o),
    }
