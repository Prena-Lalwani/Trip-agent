import operator
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class TravelState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    intent: str              # "travel" | "chat" — set by router_node

    # Extracted travel metadata
    destination: str
    travel_dates: str
    budget: str
    duration: str
    number_of_travelers: str
    travel_style: str

    # Per-agent queries designed by extractor ("" means skip that agent)
    weather_query: str
    info_query: str
    planner_query: str

    # Agent outputs
    weather_data: str
    destination_info: str
    travel_plan: str
    final_response: str

    # Token usage — operator.add accumulates across every node automatically
    input_tokens: Annotated[int, operator.add]
    output_tokens: Annotated[int, operator.add]
    total_tokens: Annotated[int, operator.add]
