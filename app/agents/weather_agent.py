from pathlib import Path

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import TravelState
from app.core.config import settings
from app.core.token_tracker import TokenTracker
from app.tools.weather_tools import get_current_weather, get_weather_forecast

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.google_api_key,
    temperature=0.3,
)

_tools = [get_current_weather, get_weather_forecast]

_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            Path("app/prompts/weather_agent.txt").read_text(encoding="utf-8"),
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

_executor = AgentExecutor(
    agent=create_tool_calling_agent(_llm, _tools, _prompt),
    tools=_tools,
    verbose=False,
)


async def weather_node(state: TravelState) -> dict:
    query = state.get("weather_query", "").strip()
    if not query:
        return {"weather_data": "", "input_tokens": 0,
                "output_tokens": 0, "total_tokens": 0}

    tracker = TokenTracker()
    result = await _executor.ainvoke(
        {"input": query}, config={"callbacks": [tracker]}
    )
    return {
        "weather_data": result["output"],
        "input_tokens": tracker.input_tokens,
        "output_tokens": tracker.output_tokens,
        "total_tokens": tracker.total_tokens,
    }