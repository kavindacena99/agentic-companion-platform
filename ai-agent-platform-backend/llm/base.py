"""LLM provider interface.

Every concrete provider (OpenAI, Gemini, ...) implements this contract so the
rest of the system stays provider-agnostic. The orchestrator (``llm_router``)
is the only thing that selects between them.
"""

from abc import ABC, abstractmethod
from typing import Any


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
