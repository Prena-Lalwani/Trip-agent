from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.aggregator import aggregator_node
from app.agents.extractor import extractor_node
from app.agents.info_agent import info_node
from app.agents.planner_agent import planner_node
from app.agents.router import chat_node, route_by_intent, router_node
from app.agents.state import TravelState
from app.agents.weather_agent import weather_node


def build_graph():
    builder = StateGraph(TravelState)

    builder.add_node("router", router_node)
    builder.add_node("chat", chat_node)
    builder.add_node("extractor", extractor_node)
    builder.add_node("weather_agent", weather_node)
    builder.add_node("info_agent", info_node)
    builder.add_node("planner_agent", planner_node)
    builder.add_node("aggregator", aggregator_node)

    # Router runs first — decides travel vs. chat
    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        route_by_intent,
        {"travel": "extractor", "chat": "chat"},
    )

    # Chat path ends immediately
    builder.add_edge("chat", END)

    # Travel path: extract → parallel agents → planner → aggregator
    builder.add_edge("extractor", "weather_agent")
    builder.add_edge("extractor", "info_agent")
    builder.add_edge("weather_agent", "planner_agent")
    builder.add_edge("info_agent", "planner_agent")
    builder.add_edge("planner_agent", "aggregator")
    builder.add_edge("aggregator", END)

    return builder.compile(checkpointer=MemorySaver())


travel_graph = build_graph()
