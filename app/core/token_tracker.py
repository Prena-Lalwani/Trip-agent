from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class TokenTracker(BaseCallbackHandler):
    """Accumulates token usage across every LLM call in a single graph run."""

    def __init__(self):
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self._total_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        for generations in response.generations:
            for generation in generations:
                meta = getattr(
                    getattr(generation, "message", None), "usage_metadata", None
                )
                if meta:
                    i = meta.get("input_tokens", 0)
                    o = meta.get("output_tokens", 0)
                    self.input_tokens += i
                    self.output_tokens += o
                    self._total_tokens += meta.get("total_tokens", i + o)
