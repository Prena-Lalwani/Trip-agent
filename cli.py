import asyncio
import itertools
import uuid
import warnings

# Silence noisy third-party warnings before any imports trigger them
warnings.filterwarnings("ignore", message="No parser was explicitly specified")

from langchain_core.messages import AIMessageChunk, HumanMessage  # noqa: E402

# Import config first — sets LangSmith env vars before any LangChain code runs
import app.core.config  # noqa: F401 E402 — sets LangSmith env vars on import
from app.agents.graph import travel_graph  # noqa: E402

_NODE_LABELS = {
    "router": [
        "Thinking...",
        "Analyzing your request...",
        "Understanding context...",
    ],
    "extractor": [
        "Extracting travel details...",
        "Parsing destinations...",
        "Identifying your preferences...",
    ],
    "weather_agent": [
        "Fetching weather data...",
        "Checking forecasts...",
        "Analyzing climate conditions...",
        "Looking up temperatures...",
    ],
    "info_agent": [
        "Researching destination...",
        "Looking up attractions...",
        "Finding local tips...",
        "Searching travel guides...",
    ],
    "planner_agent": [
        "Creating your travel plan...",
        "Building your itinerary...",
        "Optimizing day by day...",
        "Planning activities...",
    ],
    "aggregator": [
        "Formatting response...",
        "Putting it all together...",
        "Almost there...",
    ],
}

_CYCLE_INTERVAL = 4.0  # seconds between label changes


async def _cycle_labels(labels: list[str]) -> None:
    """Print the first label immediately, then cycle through the rest every N seconds."""
    for label in itertools.cycle(labels):
        print(f"  {label}", flush=True)
        await asyncio.sleep(_CYCLE_INTERVAL)


async def chat_loop():
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("\n========================================")
    print("   AI Travel Planner  (type 'exit' to quit)")
    print("========================================\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye! Happy travels!")
            break

        inputs = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
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

        print("\nAssistant:\n")
        seen_nodes: set[str] = set()
        cycle_task: asyncio.Task | None = None

        async for chunk, metadata in travel_graph.astream(
            inputs, config=config, stream_mode="messages"
        ):
            node = metadata.get("langgraph_node", "")

            # New node detected — stop old cycling, start new one
            if node in _NODE_LABELS and node not in seen_nodes:
                seen_nodes.add(node)
                if cycle_task and not cycle_task.done():
                    cycle_task.cancel()
                cycle_task = asyncio.create_task(
                    _cycle_labels(_NODE_LABELS[node])
                )

            # Tokens flowing in — stop cycling and stream text
            if node in ("aggregator", "chat"):
                if cycle_task and not cycle_task.done():
                    cycle_task.cancel()
                    cycle_task = None
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    print(chunk.content, end="", flush=True)

        # Clean up if still running after stream ends
        if cycle_task and not cycle_task.done():
            cycle_task.cancel()

        print("\n")

        final_state = await travel_graph.aget_state(config)
        vals = final_state.values if final_state else {}
        print(
            f"  [Tokens] input: {vals.get('input_tokens', 0)}  "
            f"output: {vals.get('output_tokens', 0)}  "
            f"total: {vals.get('total_tokens', 0)}\n"
        )


if __name__ == "__main__":
    asyncio.run(chat_loop())
