"""Query planning + relevance grading for the self-correcting retrieval loop.

Deterministic, dependency-free helpers (no LLM) that drive the Agentic-RAG
retrieve → grade → reformulate cycle:

* :func:`plan_query`        — turn a raw user message into a focused search query.
* :func:`reformulate_query` — produce a *different*, progressively broader query
  when a first pass retrieves weak candidates.
* :func:`grade_memories`    — judge whether retrieved memories are good enough to
  ground a response, using the normalized ``relevance`` scores the hybrid
  retriever attaches (see ``memory/memory_retriever.py``).

Keeping these pure and rule-based makes the loop's control flow trivially
testable and means retrieval never depends on a model being reachable.
"""

import re
from typing import Any, Dict, List, Optional

# A memory counts as a strong hit when its normalized relevance clears this bar.
# ``relevance`` is cosine-similarity-derived in ``[0, 1]``; 0.35 keeps clearly
# on-topic memories while rejecting incidental token overlap.
GRADE_RELEVANCE_THRESHOLD = 0.35

# How many strong hits are needed to call a retrieval pass "sufficient".
GRADE_MIN_STRONG_HITS = 1

# Common words that carry no retrieval signal — dropped when planning a query.
_STOPWORDS = frozenset(
    """
    a an and the of to in on at for is are am was were be been being do does did
    i you he she it we they me my your his her its our their this that these those
    can could would should will shall may might must have has had how what why when
    where who which whom with about from into over under again just so very really
    please tell talk say know think want need get got make made give
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9']+")

# Affect / intent labels that carry no useful retrieval signal as query hints.
_UNINFORMATIVE_HINTS = frozenset({"neutral", "casual", "unknown", ""})


def _tokens(text: Optional[str]) -> List[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _keywords(message: str) -> List[str]:
    """Salient, order-preserving, de-duplicated keywords from ``message``."""
    seen: List[str] = []
    for token in _tokens(message):
        if token in _STOPWORDS or len(token) < 2:
            continue
        if token not in seen:
            seen.append(token)
    return seen


def plan_query(message: str) -> str:
    """Rewrite ``message`` into a focused keyword search query.

    Strips filler/stopwords so the first retrieval pass targets the salient
    terms. Falls back to the trimmed original when nothing salient remains
    (e.g. a very short message), so we never search on an empty string.
    """
    keywords = _keywords(message)
    if keywords:
        return " ".join(keywords)
    return (message or "").strip()


def reformulate_query(
    message: str,
    iteration: int,
    emotion: Optional[str] = None,
    intent: Optional[str] = None,
) -> str:
    """Produce an improved, *different* query for retry ``iteration`` (1-based).

    The strategy widens progressively: first fall back to the full original
    message (broader context than bare keywords), then enrich the keywords with
    affect/intent hints. Deterministic so the loop is reproducible and testable.
    """
    keywords = _keywords(message)
    hints = [
        hint
        for hint in (emotion, intent)
        if hint and hint.lower() not in _UNINFORMATIVE_HINTS
    ]

    variants = [
        (message or "").strip(),                    # 1st retry: broaden to full text
        " ".join(keywords + hints),                 # 2nd retry: add affect/intent
        " ".join(dict.fromkeys(keywords + _tokens(message))),  # later: union of all
    ]
    index = min(max(iteration - 1, 0), len(variants) - 1)
    return variants[index] or (message or "").strip()


def grade_memories(
    retrieved: List[Dict[str, Any]],
    threshold: float = GRADE_RELEVANCE_THRESHOLD,
    min_strong_hits: int = GRADE_MIN_STRONG_HITS,
) -> str:
    """Grade a retrieval pass as ``"sufficient"`` or ``"insufficient"``.

    Heuristic over the normalized ``relevance`` scores: a pass is sufficient once
    at least ``min_strong_hits`` memories clear ``threshold``. Empty results are
    always insufficient.
    """
    if not retrieved:
        return "insufficient"
    strong = sum(1 for item in retrieved if float(item.get("relevance") or 0.0) >= threshold)
    return "sufficient" if strong >= min_strong_hits else "insufficient"


def best_relevance(retrieved: List[Dict[str, Any]]) -> float:
    """Highest normalized relevance in ``retrieved`` (0.0 when empty)."""
    if not retrieved:
        return 0.0
    return max(float(item.get("relevance") or 0.0) for item in retrieved)
