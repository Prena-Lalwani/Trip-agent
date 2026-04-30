from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import TravelState
from app.core.config import settings

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.google_api_key,
    temperature=0.7,
)

_system_prompt = Path("app/prompts/planner_agent.txt").read_text(encoding="utf-8")


async def planner_node(state: TravelState) -> dict:
    query = state.get("planner_query", "").strip()
    if not query:
        return {"travel_plan": "", "input_tokens": 0,
                "output_tokens": 0, "total_tokens": 0}

    weather = state.get("weather_data", "").strip()
    info = state.get("destination_info", "").strip()

    context_parts = []
    if weather:
        context_parts.append(f"--- Weather Data ---\n{weather}")
    if info:
        context_parts.append(f"--- Destination Info ---\n{info}")

    system_content = _system_prompt
    if context_parts:
        system_content += "\n\n" + "\n\n".join(context_parts)

    messages = [
        SystemMessage(content=system_content),
        *state["messages"][:-1],
        HumanMessage(content=query),
    ]
    response = await _llm.ainvoke(messages)
    usage = response.usage_metadata or {}
    i = usage.get("input_tokens", 0)
    o = usage.get("output_tokens", 0)
    return {
        "travel_plan": response.content,
        "input_tokens": i,
        "output_tokens": o,
        "total_tokens": usage.get("total_tokens", i + o),
    }