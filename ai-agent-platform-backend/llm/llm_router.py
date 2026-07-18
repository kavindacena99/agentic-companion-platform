"""LLM orchestrator — the central brain that selects a provider and runs it.

All LLM calls in the system go through here. Providers are chosen by the needs
expressed in ``context`` (quality vs. cost), and if the preferred provider is
unavailable or fails, the router automatically falls back to the next one.

Selection rules:
    * high quality needed  -> OpenAI first, Gemini fallback
    * low cost preferred   -> Gemini first, OpenAI fallback
    * a provider failure    -> automatically try the next available provider
"""

import logging
from typing import Any, Dict, List

from llm.base import LLMProvider
from llm.gemini_provider import GeminiProvider
from llm.openai_provider import OpenAIProvider

logger = logging.getLogger("agent_core")

# Safe response used only when every provider is unavailable or fails, so the
# pipeline degrades gracefully instead of crashing.
_FALLBACK_RESPONSE = (
    "I'm having trouble responding right now, but I'm still here with you. "
    "Could you try saying that again in a moment?"
)


class LLMRouter:
    def __init__(self, providers: Dict[str, LLMProvider] | None = None):
        self.providers: Dict[str, LLMProvider] = providers or {
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
        }

    def _provider_order(self, context: Dict[str, Any]) -> List[str]:
        """Decide provider priority from the request context."""
        intent = (context or {}).get("intent")
        quality = (context or {}).get("quality")

        # Crisis or explicitly high-quality work prefers the strongest model.
        high_quality = quality == "high" or intent == "crisis"
        # Explicit low-cost preference flips the order.
        low_cost = quality == "low"

        if low_cost and not high_quality:
            return ["gemini", "openai"]
        return ["openai", "gemini"]

    def route(self, prompt: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Run ``prompt`` through the best available provider with fallback.

        Returns ``{provider, response, ok}``. ``ok`` is ``False`` (with a safe
        fallback response) when no provider could produce an answer.
        """
        context = context or {}
        order = self._provider_order(context)

        for name in order:
            provider = self.providers.get(name)
            if provider is None or not provider.is_available():
                continue
            try:
                text = provider.generate(prompt, **context.get("llm_kwargs", {}))
                logger.info("LLM response generated via provider '%s'", name)
                return {"provider": name, "response": text, "ok": True}
            except Exception as exc:  # noqa: BLE001 — fall back on any provider error
                logger.warning("Provider '%s' failed, falling back: %s", name, exc)
                continue

        logger.error("No LLM provider was available; returning safe fallback response.")
        return {"provider": "none", "response": _FALLBACK_RESPONSE, "ok": False}

    def route_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Run one function-calling turn through the best tool-capable provider.

        Only providers advertising ``supports_tools()`` are considered (OpenAI
        today; Gemini is guarded out until its function-calling adapter lands),
        tried in quality order with fallback. Returns the provider's normalized
        result plus ``{provider, ok}``. When no tool-capable provider is usable
        or all fail, returns ``{"ok": False}`` so the caller can degrade to plain
        text generation instead of crashing.
        """
        context = context or {}
        order = self._provider_order(context)

        for name in order:
            provider = self.providers.get(name)
            if provider is None or not provider.supports_tools():
                continue
            try:
                result = provider.generate_with_tools(
                    messages, tools, **context.get("llm_kwargs", {})
                )
                result["provider"] = name
                result["ok"] = True
                logger.info("Tool-calling turn handled via provider '%s'", name)
                return result
            except Exception as exc:  # noqa: BLE001 — fall back on any provider error
                logger.warning("Tool provider '%s' failed, falling back: %s", name, exc)
                continue

        logger.warning("No tool-capable provider was available.")
        return {"provider": "none", "ok": False}


# Shared default router instance + module-level convenience function.
_default_router = LLMRouter()


def route_llm(prompt: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Module-level entry point: route ``prompt`` using the default router."""
    return _default_router.route(prompt, context)


def route_tools(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Module-level entry point: run a tool-calling turn via the default router."""
    return _default_router.route_tools(messages, tools, context)
