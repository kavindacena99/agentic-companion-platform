"""OpenAI LLM adapter.

Wraps the OpenAI SDK behind the :class:`LLMProvider` interface. The SDK and the
API key are resolved lazily so importing this module never fails and never
makes a network call — `is_available()` is safe to probe.
"""

import logging
import os
from typing import Any, Optional

from llm.base import LLMProvider

logger = logging.getLogger("agent_core")


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = None

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import openai  # noqa: F401
        except ImportError:
            return False
        return True

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, **kwargs: Any) -> str:
        if not self.is_available():
            raise RuntimeError("OpenAIProvider is not configured (missing API key or SDK).")

        client = self._get_client()
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 600)

        response = client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (response.choices[0].message.content or "").strip()
