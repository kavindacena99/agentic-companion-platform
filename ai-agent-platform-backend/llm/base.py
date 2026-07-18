"""LLM provider interface.

Every concrete provider (OpenAI, Gemini, ...) implements this contract so the
rest of the system stays provider-agnostic. The orchestrator (``llm_router``)
is the only thing that selects between them.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    #: Short identifier used in routing / logging (overridden by subclasses).
    name: str = "base"

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Return the model's text completion for ``prompt``."""
        raise NotImplementedError

    def is_available(self) -> bool:
        """Whether this provider is configured and usable right now.

        Used by the router to skip unconfigured providers without raising.
        Subclasses should override (e.g. check for an API key / installed SDK).
        """
        return False

    # ------------------------------------------------------------------
    # Tool / function calling (optional capability)
    # ------------------------------------------------------------------
    def supports_tools(self) -> bool:
        """Whether this provider implements :meth:`generate_with_tools`.

        Defaults to ``False`` so providers without function-calling are simply
        skipped by the tool router. Providers opt in by overriding this.
        """
        return False

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Run one function-calling turn over ``messages`` with ``tools`` available.

        Returns a **normalized** dict, independent of any vendor SDK:

        * ``{"type": "tool_calls", "tool_calls": [{"id", "name", "arguments"}],
          "raw_message": <provider assistant message>}`` — the model wants to
          call one or more tools; ``arguments`` is a parsed ``dict``.
        * ``{"type": "text", "text": <str>}`` — the model produced a final answer.

        Providers that do not support tools should leave this raising.
        """
        raise NotImplementedError(f"{self.name} does not support tool calling.")
