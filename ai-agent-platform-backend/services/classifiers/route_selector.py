"""Route selector — decides which pipeline path a message takes.

Deterministic and rule-based (no LLM): it reuses the intent classifier's verdict
and a small tool-need heuristic to pick one of :data:`ROUTE_TYPES`. Keeping this
a pure function (independent of LangGraph) makes the routing policy trivially
unit-testable; the ``router`` graph node is a thin wrapper over it.

Routing policy:

* ``crisis``   — a safety signal; take the deterministic fast-path (no LLM).
* ``tool``     — the turn needs external/real-time data a tool must fetch.
* ``retrieve`` — a knowledge / emotional turn that benefits from memory context.
* ``direct``   — trivial small-talk; answer directly, skipping retrieval.
"""

import re
from typing import List

ROUTE_CRISIS = "crisis"
ROUTE_DIRECT = "direct"
ROUTE_RETRIEVE = "retrieve"
ROUTE_TOOL = "tool"

ROUTE_TYPES: List[str] = [ROUTE_CRISIS, ROUTE_DIRECT, ROUTE_RETRIEVE, ROUTE_TOOL]

# Intents (from the intent classifier) that warrant memory retrieval.
_RETRIEVE_INTENTS = {"question", "emotional"}

# Explicit action / external-data needs a tool would satisfy. Deliberately
# narrow so we only divert clear tool cases away from ordinary retrieval. These
# mirror the built-in tools (set_reminder, suggest_activity, search_web).
_TOOL_PATTERNS = [
    # set_reminder
    r"\bremind me\b",
    r"\bset (?:a |an )?reminder\b",
    r"\breminder to\b",
    # suggest_activity
    r"\bsuggest (?:an? )?activit\w*\b",
    r"\bwhat should i do\b",
    r"\b(?:i'?m|i am) bored\b",
    r"\bgive me (?:an? )?idea\b",
    # search_web / real-time data
    r"\bweather\b",
    r"\bforecast\b",
    r"\bwhat time is it\b",
    r"\btime (?:in|at)\b",
    r"\bsearch (?:the )?(?:web|internet|online)\b",
    r"\blook (?:it |this )?up\b",
    r"\blatest news\b",
    r"\bstock price\b",
    r"\bexchange rate\b",
]


def _needs_tool(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in _TOOL_PATTERNS)


def select_route(intent: str, message: str) -> str:
    """Pick a pipeline route from the classified ``intent`` and raw ``message``.

    ``crisis`` always wins (safety first). Otherwise an explicit tool need routes
    to ``tool``; knowledge/emotional intents route to ``retrieve``; everything
    else answers ``direct``.
    """
    if intent == "crisis":
        return ROUTE_CRISIS

    text = (message or "").lower()
    if _needs_tool(text):
        return ROUTE_TOOL

    if intent in _RETRIEVE_INTENTS:
        return ROUTE_RETRIEVE

    return ROUTE_DIRECT
