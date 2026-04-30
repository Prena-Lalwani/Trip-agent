import asyncio
import uuid
from datetime import datetime

from langchain_core.messages import HumanMessage

import app.core.config  # noqa: F401 — sets LangSmith env vars on import
from app.agents.graph import travel_graph

# Each entry: (label, query, expected agents)
REQUESTS = [
    (
        "Kashmir — Weather Only",
        "What is the current weather in Kashmir right now? "
        "What should I pack and what's the best time of day to go outside?",
    ),
    (
        "Murree — Info Only",
        "Tell me about the top attractions, must-try local food, "
        "and estimated daily costs for a trip to Murree.",
    ),
    (
        "Sharan — Planner Only",
        "The weather in Sharan is pleasant and cool. "
        "I already know it has dense forests and waterfalls. "
        "Create a detailed 3-day itinerary for a solo nature trip to Sharan "
        "without researching weather or destination info again.",
    ),
    (
        "Swat — All Agents",
        "I want to plan a full 2-week Eid trip to Swat. "
        "Get the weather forecast, research top attractions and local food, "
        "and then build a complete day-by-day travel plan.",
    ),
]

DIVIDER = "=" * 60


async def run_request(label: str, user_query: str) -> dict:
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "weather_query": "",
        "info_query": "",
        "planner_query": "",
        "weather_data": "",
        "destination_info": "",
        "travel_plan": "",
        "final_response": "",
    }

    start = datetime.now()
    print(f"[{label}] Started  at {start.strftime('%H:%M:%S')}")
    result = await travel_graph.ainvoke(inputs, config=config)
    end = datetime.now()
    elapsed = (end - start).total_seconds()
    print(f"[{label}] Finished at {end.strftime('%H:%M:%S')}  ({elapsed:.1f}s)")
    return {
        "label": label,
        "response": result.get("final_response", ""),
        "start": start.strftime("%H:%M:%S"),
        "end": end.strftime("%H:%M:%S"),
        "elapsed": elapsed,
    }


async def main():
    print(f"\n{DIVIDER}")
    print("  Parallel Requests — 4 Queries, Different Agent Combinations")
    print(f"  1. Kashmir  → weather agent only")
    print(f"  2. Murree   → info agent only")
    print(f"  3. Sharan   → planner agent only")
    print(f"  4. Swat     → all 3 agents")
    print(f"{DIVIDER}\n")

    tasks = [run_request(label, query) for label, query in REQUESTS]
    results = await asyncio.gather(*tasks)

    print(f"\n{DIVIDER}")
    print("  Timing Summary")
    print(DIVIDER)
    for r in results:
        print(
            f"  {r['label']:<35} "
            f"start={r['start']}  end={r['end']}  "
            f"({r['elapsed']:.1f}s)"
        )
    print(f"{DIVIDER}\n")

    for r in results:
        print(f"## {r['label']}\n")
        print(r["response"])
        print(f"\n{'-' * 60}\n")


if __name__ == "__main__":
    asyncio.run(main())
