"""Google Gemini LLM adapter.

Wraps the ``google-generativeai`` SDK behind the :class:`LLMProvider`
interface. The SDK is optional — if it is not installed, ``is_available()``
returns ``False`` and the router simply skips this provider.
"""

import logging
import os
from typing import Any, Optional

from llm.base import LLMProvider

logger = logging.getLogger("agent_core")


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import google.generativeai  # noqa: F401
        except ImportError:
            return False
        return True

    def generate(self, prompt: str, **kwargs: Any) -> str:
        if not self.is_available():
            raise RuntimeError(
                "GeminiProvider is not configured (missing API key or SDK)."
            )

        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(kwargs.get("model", self.model))
        response = model.generate_content(prompt)
        return (getattr(response, "text", "") or "").strip()
