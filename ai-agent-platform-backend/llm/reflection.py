"""Generation self-reflection — a cheap-model critic over a draft reply.

Sits between generation and the deterministic safety gate. It asks a *cheap*
LLM whether a draft response is (1) grounded in the retrieved memories,
(2) in-persona, and (3) responsive to the user's emotion, and returns a verdict
of ``accept`` or ``revise`` plus a short critique the next generation attempt can
act on.

This is a **quality** check, not a safety check: it is best-effort and fails
*open* (``accept``) whenever the critic model is unavailable or its output can't
be parsed, so it can never block a reply on its own. The deterministic
:class:`safety.engine.SafetyEngine` remains the always-run final gate.
"""

import logging
import re
from typing import Any, Callable, Dict, List, Optional

from llm.llm_router import route_llm

logger = logging.getLogger("agent_core")

# Verdict tokens.
ACCEPT = "accept"
REVISE = "revise"

# How many memory snippets to show the critic (keeps the prompt cheap).
_MAX_SNIPPETS = 6


def _memory_snippets(memories: List[Dict[str, Any]]) -> str:
    lines = []
    for item in (memories or [])[:_MAX_SNIPPETS]:
        content = (item or {}).get("content")
        if content:
            lines.append(f"- {content}")
    return "\n".join(lines) if lines else "(no memories retrieved)"


def build_reflection_prompt(
    message: str,
    draft: str,
    memories: List[Dict[str, Any]],
    persona: str,
    emotion: Optional[str],
) -> str:
    """Assemble the critic prompt. Kept small so a cheap model is enough."""
    return (
        "You are a strict reviewer of an AI companion's draft reply. "
        "Judge ONLY these three things:\n"
        "1) GROUNDED: every claim about the user is supported by the memories below "
        "(no invented facts).\n"
        "2) IN-PERSONA: the reply matches the persona.\n"
        "3) EMOTION: the reply acknowledges the user's emotional state.\n\n"
        f"[PERSONA]\n{persona or '(none)'}\n\n"
        f"[RETRIEVED MEMORIES]\n{_memory_snippets(memories)}\n\n"
        f"[DETECTED EMOTION]\n{emotion or 'neutral'}\n\n"
        f"[USER MESSAGE]\n{message or ''}\n\n"
        f"[DRAFT REPLY]\n{draft or ''}\n\n"
        "Answer in EXACTLY this format:\n"
        "VERDICT: ACCEPT or REVISE\n"
        "REASON: <one sentence; if REVISE, say what to fix>"
    )


def _parse_reflection(text: str) -> Dict[str, str]:
    """Extract ``{verdict, critique}`` from the critic's output (fail-open)."""
    verdict = ACCEPT
    match = re.search(r"VERDICT\s*[:\-]?\s*(ACCEPT|REVISE)", text or "", re.IGNORECASE)
    if match:
        verdict = match.group(1).lower()
    elif re.search(r"\brevise\b", text or "", re.IGNORECASE):
        verdict = REVISE

    critique = ""
    reason = re.search(r"REASON\s*[:\-]?\s*(.+)", text or "", re.IGNORECASE)
    if reason:
        critique = reason.group(1).strip()
    return {"verdict": verdict, "critique": critique}


def reflect_on_response(
    message: str,
    draft: str,
    memories: List[Dict[str, Any]],
    persona: str,
    emotion: Optional[str] = None,
    router: Callable[..., Dict[str, Any]] = route_llm,
) -> Dict[str, Any]:
    """Critique ``draft`` and return ``{verdict, critique, ok}``.

    Uses a low-cost provider. Any failure (no provider, exception, empty output)
    yields ``verdict=accept`` with ``ok=False`` so reflection never blocks a
    reply — the deterministic safety engine is the real gate.
    """
    if not (draft or "").strip():
        return {"verdict": ACCEPT, "critique": "", "ok": False}

    prompt = build_reflection_prompt(message, draft, memories, persona, emotion)
    try:
        result = router(prompt, {"quality": "low", "intent": "reflection"})
    except Exception as exc:  # noqa: BLE001 — reflection must never crash the graph
        logger.warning("Reflection failed, accepting draft: %s", exc)
        return {"verdict": ACCEPT, "critique": "", "ok": False}

    if not result.get("ok"):
        # No provider produced a real judgment — fail open.
        return {"verdict": ACCEPT, "critique": "", "ok": False}

    parsed = _parse_reflection(result.get("response", ""))
    parsed["ok"] = True
    logger.debug("Reflection verdict=%s", parsed["verdict"])
    return parsed
