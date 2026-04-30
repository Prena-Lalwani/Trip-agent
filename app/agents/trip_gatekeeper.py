import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.google_api_key,
    temperature=0,
)

_SYSTEM = """\
You are a gatekeeper for a Travel Agent AI inside a group trip planning chat.
Decide if the Travel Agent should respond to the latest message.

Say YES if:
- A travel question is asked that no one has answered yet
- The group has genuine uncertainty about destination, dates, weather,
  costs, packing, or logistics
- The group is debating a travel decision where data would help

Say NO if:
- Pure social chat ("ok", "sure", "haha", greetings, emojis)
- The Travel Agent already replied within the last 3 messages
- Someone already gave a satisfactory answer
- Personal coordination not related to travel

Respond ONLY with valid JSON, no extra text:
{"should_respond": true, "question": "the specific question to answer"}
or
{"should_respond": false, "question": ""}
"""


async def check(
    messages: list[dict], new_message: str
) -> tuple[bool, str]:
    """Return (should_respond, question_to_answer).

    @agent anywhere in the message is a hard-YES override — skip the LLM.
    """
    if "@agent" in new_message.lower():
        question = new_message.replace("@agent", "").strip() or new_message
        return True, question

    history_lines = "\n".join(
        f"[Travel Agent]: {m['content']}"
        if m.get("is_agent")
        else f"{m['user_email']}: {m['content']}"
        for m in messages
    )
    prompt = (
        f"Chat history (oldest first):\n{history_lines}"
        f"\n\nLatest message: {new_message}"
    )

    response = await _llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=prompt),
    ])

    try:
        raw = response.content.strip()
        # Strip markdown code fences if model wraps in ```json ... ```
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        return bool(data.get("should_respond")), data.get("question", new_message)
    except Exception:
        return False, ""
