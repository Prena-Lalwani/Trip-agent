import json
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import TravelState
from app.core.config import settings

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.google_api_key,
    temperature=0,
)

_prompt_template = Path("app/prompts/extractor.txt").read_text(encoding="utf-8")


async def extractor_node(state: TravelState) -> dict:
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    system_prompt = _prompt_template.replace("{current_date}", current_date)

    history = state.get("messages", [])
    response = await _llm.ainvoke([
        SystemMessage(content=system_prompt),
        *history[:-1],           # previous turns for context
        HumanMessage(content=state["user_query"]),
    ])

    usage = response.usage_metadata or {}
    i = usage.get("input_tokens", 0)
    o = usage.get("output_tokens", 0)
    token_update = {"input_tokens": i, "output_tokens": o, "total_tokens": usage.get("total_tokens", i + o)}

    try:
        content = response.content
        start, end = content.find("{"), content.rfind("}") + 1
        data = json.loads(content[start:end])
        return {
            "destination":         data.get("destination", ""),
            "travel_dates":        data.get("travel_dates", ""),
            "budget":              data.get("budget", ""),
            "duration":            data.get("duration", ""),
            "number_of_travelers": data.get("number_of_travelers", ""),
            "travel_style":        data.get("travel_style", ""),
            "weather_query":       data.get("weather_query", ""),
            "info_query":          data.get("info_query", ""),
            "planner_query":       data.get("planner_query", ""),
            **token_update,
        }
    except Exception:
        return {
            "destination": "", "travel_dates": "", "budget": "",
            "duration": "", "number_of_travelers": "", "travel_style": "",
            "weather_query": "", "info_query": "",
            "planner_query": state["user_query"],
            **token_update,
        }