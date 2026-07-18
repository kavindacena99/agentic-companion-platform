"""Memory retriever — hybrid similarity search + re-ranking.

Converts a query into an embedding and runs a metadata-filtered dense search
against a ChromaDB collection, always scoped to a single ``user_id`` /
``agent_id`` so memories never leak across users or agents.

On top of the dense (vector) signal it applies an optional, dependency-free
lexical **BM25** signal and re-ranks a candidate pool, then returns the best
``top_k`` results. Every result carries a **normalized relevance score** in
``[0, 1]`` (higher = more relevant) so a downstream grader / corrective-retrieval
loop can reason about candidate quality without knowing about cosine distance.

Hybrid scoring::

    relevance = alpha * dense_score + (1 - alpha) * lexical_score

where ``dense_score`` is cosine similarity clamped to ``[0, 1]`` and
``lexical_score`` is a max-normalized BM25 score over the candidate pool. When
the query has no usable terms (or nothing overlaps lexically) the score falls
back cleanly to the dense signal alone.
"""

import logging
import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional

from memory.collections import get_collection
from memory.embeddings import generate_embedding

logger = logging.getLogger("agent_core")

# Weight of the dense (semantic) signal in the hybrid score. The lexical
# (BM25) signal gets the remaining ``1 - alpha``. Semantic is favored because
# embeddings generalize past exact wording; lexical rescues keyword/entity hits.
DEFAULT_ALPHA = 0.7

# BM25 tuning constants (standard defaults).
_BM25_K1 = 1.5
_BM25_B = 0.75

# Tokenizer for the lexical signal: lowercase alphanumeric runs.
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _build_where(user_id: str, agent_id: str, extra: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a Chroma ``where`` filter (uses ``$and`` for multiple conditions).

    ``user_id`` and ``agent_id`` scoping is mandatory and always applied first,
    so extra caller-supplied filters can never widen access beyond one user/agent.
    """
    conditions: List[Dict[str, Any]] = [
        {"user_id": user_id},
        {"agent_id": agent_id},
    ]
    if extra:
        conditions.extend({key: value} for key, value in extra.items())
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def _tokenize(text: Optional[str]) -> List[str]:
    """Split text into lowercase alphanumeric tokens for the lexical signal."""
    return _TOKEN_RE.findall((text or "").lower())


def _distance_to_similarity(distance: Optional[float]) -> float:
    """Map a cosine ``distance`` to a relevance score in ``[0, 1]``.

    Collections use cosine space, where ``distance = 1 - cosine_similarity``.
    We therefore recover the similarity and clamp negatives to 0, so the result
    is directly interpretable as "how relevant" (1 = identical, 0 = unrelated).
    A missing distance is treated as unknown/neutral relevance (0.0).
    """
    if distance is None:
        return 0.0
    return max(0.0, min(1.0, 1.0 - float(distance)))


def _bm25_scores(query: str, documents: List[Optional[str]]) -> List[float]:
    """Compute BM25 scores for ``documents`` against ``query``.

    Scores are computed *within the candidate pool* (the pool's own document
    frequencies / average length), which is exactly what re-ranking needs. Raw
    BM25 scores are returned; callers normalize. Returns all-zeros when there is
    nothing to score (empty query or no documents).
    """
    query_terms = _tokenize(query)
    if not query_terms or not documents:
        return [0.0] * len(documents)

    doc_tokens = [_tokenize(doc) for doc in documents]
    doc_lengths = [len(tokens) for tokens in doc_tokens]
    total_docs = len(documents)
    avg_length = (sum(doc_lengths) / total_docs) if total_docs else 0.0

    # Document frequency of each distinct query term within the pool.
    doc_frequency: Dict[str, int] = {}
    for term in set(query_terms):
        doc_frequency[term] = sum(1 for tokens in doc_tokens if term in tokens)

    scores: List[float] = []
    for tokens, length in zip(doc_tokens, doc_lengths):
        counts = Counter(tokens)
        score = 0.0
        for term in query_terms:
            term_freq = counts.get(term, 0)
            if term_freq == 0:
                continue
            n_qi = doc_frequency.get(term, 0)
            # Probabilistic IDF (always positive via the +1 inside the log).
            idf = math.log(1 + (total_docs - n_qi + 0.5) / (n_qi + 0.5))
            denom = term_freq + _BM25_K1 * (
                1 - _BM25_B + _BM25_B * (length / avg_length if avg_length else 0.0)
            )
            score += idf * (term_freq * (_BM25_K1 + 1)) / denom
        scores.append(score)
    return scores


def _normalize(scores: List[float]) -> List[float]:
    """Max-normalize non-negative scores into ``[0, 1]`` (all-zero stays zero)."""
    peak = max(scores) if scores else 0.0
    if peak <= 0.0:
        return [0.0] * len(scores)
    return [score / peak for score in scores]


def _hybrid_rank(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int,
    hybrid: bool,
    alpha: float,
) -> List[Dict[str, Any]]:
    """Score, re-rank and truncate the dense candidate pool.

    Each returned candidate is annotated with ``dense_score``, ``lexical_score``
    and a combined normalized ``relevance`` in ``[0, 1]``. When ``hybrid`` is off
    (or nothing overlaps lexically) the relevance equals the dense score.
    """
    if not candidates:
        return []

    dense_scores = [_distance_to_similarity(item.get("distance")) for item in candidates]

    if hybrid:
        documents = [item.get("content") for item in candidates]
        lexical_scores = _normalize(_bm25_scores(query, documents))
    else:
        lexical_scores = [0.0] * len(candidates)

    lexical_present = any(score > 0.0 for score in lexical_scores)
    for item, dense, lexical in zip(candidates, dense_scores, lexical_scores):
        # Fall back to pure dense when there is no lexical signal, so a query
        # with no keyword overlap is never penalized by an all-zero lexical term.
        relevance = (alpha * dense + (1 - alpha) * lexical) if lexical_present else dense
        item["dense_score"] = round(dense, 6)
        item["lexical_score"] = round(lexical, 6)
        item["relevance"] = round(relevance, 6)

    candidates.sort(key=lambda item: item["relevance"], reverse=True)
    return candidates[:top_k]


def search_memory(
    collection_name: str,
    query: str,
    user_id: str,
    agent_id: str,
    top_k: int = 5,
    where: Optional[Dict[str, Any]] = None,
    hybrid: bool = True,
    alpha: float = DEFAULT_ALPHA,
    fetch_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return up to ``top_k`` memories most relevant to ``query``.

    Runs a metadata-filtered dense search scoped to ``user_id`` and ``agent_id``
    (plus any extra ``where`` conditions), then — when ``hybrid`` is true —
    re-ranks a larger candidate pool (``fetch_k``) with a lexical BM25 signal.

    Each result is
    ``{id, content, metadata, distance, dense_score, lexical_score, relevance}``
    where ``relevance`` is a normalized ``[0, 1]`` score (higher = more relevant)
    for a downstream grader to consume. Results are ordered by ``relevance``.
    """
    collection = get_collection(collection_name)

    # Nothing stored yet → nothing to search.
    if collection.count() == 0:
        return []

    # Pull a wider candidate pool than we return so the re-ranker has something
    # to work with; without hybrid re-ranking there is no benefit to over-fetch.
    if fetch_k is None:
        fetch_k = max(top_k * 4, 20) if hybrid else top_k
    fetch_k = max(fetch_k, top_k)

    query_embedding = generate_embedding(query)
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=fetch_k,
        where=_build_where(user_id, agent_id, where),
    )

    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    candidates: List[Dict[str, Any]] = []
    for index, record_id in enumerate(ids):
        candidates.append(
            {
                "id": record_id,
                "content": documents[index] if index < len(documents) else None,
                "metadata": metadatas[index] if index < len(metadatas) else {},
                "distance": distances[index] if index < len(distances) else None,
            }
        )

    ranked = _hybrid_rank(query, candidates, top_k, hybrid, alpha)

    logger.debug(
        "search_memory(%s) user=%s agent=%s hybrid=%s -> %d/%d hits",
        collection_name,
        user_id,
        agent_id,
        hybrid,
        len(ranked),
        len(candidates),
    )
    return ranked
