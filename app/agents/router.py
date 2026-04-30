from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import TravelState
from app.core.config import settings

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.google_api_key,
    temperature=0,
)


def _tokens(response) -> dict:
    usage = response.usage_metadata or {}
    i = usage.get("input_tokens", 0)
    o = usage.get("output_tokens", 0)
    return {
        "input_tokens": i,
        "output_tokens": o,
        "total_tokens": usage.get("total_tokens", i + o),
    }


async def router_node(state: TravelState) -> dict:
    """Classify the query as 'travel' or 'chat'."""
    history = state.get("messages", [])
    messages = [
        SystemMessage(
            content=(
                "You are a routing classifier for an AI travel planner. "
                "Analyze the latest user message in context of the "
                "conversation history. Decide if it requires travel planning "
                "(weather, destinations, itineraries, trip schedules, packing,"
                "costs, hotels) or is general conversation (greetings, "
                "follow-ups, opinions, small talk). "
                "Reply with only one word: travel or chat."
            )
        ),
        *history[:-1],
        HumanMessage(content=state["user_query"]),
    ]
    response = await _llm.ainvoke(messages)
    intent = response.content.strip().lower()
    return {
        "intent": "travel" if intent == "travel" else "chat",
        **_tokens(response),
    }


async def chat_node(state: TravelState) -> dict:
    """Handle non-travel queries — greetings, follow-ups, general questions."""
    messages = [
        SystemMessage(
            content=(
                "You are a friendly AI travel planner assistant. "
                "Answer the user's message naturally and conversationally. "
                "If they ask about something from earlier in the conversation,"
                "refer to the history. "
                "If they seem to want travel help, warmly invite them to ask."
            )
        ),
        *state["messages"],
    ]
    response = await _llm.ainvoke(messages)
    return {
        "final_response": response.content,
        "messages": [AIMessage(content=response.content)],
        **_tokens(response),
    }


def route_by_intent(state: TravelState) -> str:
    return state.get("intent", "chat")
