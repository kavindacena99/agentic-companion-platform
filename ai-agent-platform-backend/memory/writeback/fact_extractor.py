"""Fact extraction engine.

Pulls durable facts and emotional context out of a turn using deterministic
patterns (no LLM). Output is a list of typed memory candidates:

    [{"type": "user_fact", "content": "User is learning AI", "importance": "high"}]
"""

import re
from typing import Dict, List

from services.classifiers import detect_emotion

# (regex, template, importance). The first capture group is cleaned and slotted
# into the template. Patterns are intentionally conservative.
_FACT_PATTERNS = [
    (re.compile(r"\bmy name is ([A-Za-z][\w'-]{1,40})", re.I), "User's name is {0}", "high"),
    (re.compile(r"\bi(?:'m| am) learning ([\w ]{2,40})", re.I), "User is learning {0}", "high"),
    (re.compile(r"\bi work (as|at|in) ([\w ]{2,40})", re.I), "User works {0} {1}", "high"),
    (re.compile(r"\bi live in ([\w ,]{2,40})", re.I), "User lives in {0}", "high"),
    (re.compile(r"\bi(?:'m| am) (?:a|an) ([\w ]{2,40})", re.I), "User is a {0}", "medium"),
    (re.compile(r"\bi (?:like|love|enjoy) ([\w ]{2,40})", re.I), "User likes {0}", "medium"),
    (re.compile(r"\bi (?:hate|dislike) ([\w ]{2,40})", re.I), "User dislikes {0}", "medium"),
    (re.compile(r"\bi have (?:a|an|two|three|some)? ?([\w ]{2,40})", re.I), "User has {0}", "low"),
]

_STOP_AT = re.compile(r"\b(?:and|but|because|so|although|though|while)\b", re.I)


def _clean(fragment: str) -> str:
    """Trim a captured fragment to a tidy noun-ish phrase."""
    fragment = re.split(r"[.,!?;:]", fragment)[0]
    fragment = _STOP_AT.split(fragment)[0]
    return fragment.strip().rstrip(".")


def extract_facts(message: str, response: str) -> List[Dict]:
    """Extract durable user facts + emotional context from a turn."""
    text = message or ""
    facts: List[Dict] = []
    seen = set()

    for pattern, template, importance in _FACT_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        groups = [_clean(g) for g in match.groups()]
        if not all(groups):
            continue
        content = template.format(*groups)
        if content.lower() in seen:
            continue
        seen.add(content.lower())
        facts.append({"type": "user_fact", "content": content, "importance": importance})

    # Emotional context (only when clearly non-neutral).
    emotion = detect_emotion(text)
    if emotion != "neutral":
        facts.append(
            {
                "type": "emotional",
                "content": f"User expressed feeling {emotion}.",
                "importance": "medium",
            }
        )

    return facts
