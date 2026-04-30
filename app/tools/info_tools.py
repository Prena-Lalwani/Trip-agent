import contextlib
import io
import threading
import time

from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool

_wikipedia = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper(
        top_k_results=2,
        doc_content_chars_max=2000,
    )
)
_ddg = DuckDuckGoSearchRun()

# Serialize DDG calls to avoid rate limiting on concurrent requests
_ddg_lock = threading.Lock()
_MAX_RETRIES = 3
_RETRY_DELAY = 2  # seconds between retries


@tool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia for info about a destination or travel topic."""
    try:
        return _wikipedia.run(query)
    except Exception as e:
        return f"Wikipedia search failed: {e}"


@tool
def search_web(query: str) -> str:
    """Search the web for attractions, restaurants, travel tips, costs."""
    with _ddg_lock:
        for attempt in range(_MAX_RETRIES):
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    return _ddg.run(query)
            except Exception:
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_DELAY)
                    continue
        return ""
