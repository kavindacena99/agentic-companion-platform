"""Tests for the hybrid memory retriever (memory/memory_retriever.py).

Runs standalone (no Django DB / network / ChromaDB needed):

    python -m unittest memory.tests_retriever

The retriever's Chroma collection and embedding calls are stubbed so we can
assert scoping, hybrid re-ranking and normalized scoring deterministically.
"""

import unittest

from memory import memory_retriever
from memory.memory_retriever import (
    _bm25_scores,
    _build_where,
    _distance_to_similarity,
    _hybrid_rank,
    _normalize,
    search_memory,
)


class _FakeCollection:
    """Minimal Chroma collection stand-in backed by an in-memory list.

    Each record is ``(id, document, metadata, distance)``. ``query`` applies the
    ``where`` filter, honors ``n_results``, and returns candidates in the given
    order (already "closest first"), mirroring Chroma's response shape.
    """

    def __init__(self, records):
        self._records = records
        self.last_where = None
        self.last_n_results = None

    def count(self):
        return len(self._records)

    @staticmethod
    def _matches(metadata, where):
        if not where:
            return True
        conditions = where["$and"] if "$and" in where else [where]
        for condition in conditions:
            for key, value in condition.items():
                if metadata.get(key) != value:
                    return False
        return True

    def query(self, query_embeddings, n_results, where=None):
        self.last_where = where
        self.last_n_results = n_results
        matched = [r for r in self._records if self._matches(r[2], where)][:n_results]
        return {
            "ids": [[r[0] for r in matched]],
            "documents": [[r[1] for r in matched]],
            "metadatas": [[r[2] for r in matched]],
            "distances": [[r[3] for r in matched]],
        }


class _RetrieverTestBase(unittest.TestCase):
    """Patches ``get_collection`` and ``generate_embedding`` for the retriever."""

    def setUp(self):
        self._saved_get = memory_retriever.get_collection
        self._saved_embed = memory_retriever.generate_embedding
        memory_retriever.generate_embedding = lambda text: [0.0]

    def tearDown(self):
        memory_retriever.get_collection = self._saved_get
        memory_retriever.generate_embedding = self._saved_embed

    def _install(self, records):
        collection = _FakeCollection(records)
        memory_retriever.get_collection = lambda name: collection
        return collection


class BuildWhereTests(unittest.TestCase):
    def test_scoping_is_always_present(self):
        where = _build_where("u1", "a1", None)
        self.assertEqual(where, {"$and": [{"user_id": "u1"}, {"agent_id": "a1"}]})

    def test_extra_conditions_are_appended_not_replacing_scope(self):
        where = _build_where("u1", "a1", {"memory_type": "user"})
        self.assertIn({"user_id": "u1"}, where["$and"])
        self.assertIn({"agent_id": "a1"}, where["$and"])
        self.assertIn({"memory_type": "user"}, where["$and"])


class ScoringHelperTests(unittest.TestCase):
    def test_distance_to_similarity_bounds(self):
        self.assertEqual(_distance_to_similarity(0.0), 1.0)   # identical
        self.assertEqual(_distance_to_similarity(1.0), 0.0)   # orthogonal
        self.assertEqual(_distance_to_similarity(2.0), 0.0)   # opposite → clamped
        self.assertEqual(_distance_to_similarity(None), 0.0)  # unknown

    def test_normalize_scales_to_unit_peak(self):
        self.assertEqual(_normalize([2.0, 1.0, 0.0]), [1.0, 0.5, 0.0])

    def test_normalize_all_zero_stays_zero(self):
        self.assertEqual(_normalize([0.0, 0.0]), [0.0, 0.0])

    def test_bm25_prefers_documents_matching_query_terms(self):
        docs = [
            "I love hiking in the mountains",
            "the weather is nice",
            "hiking and mountains are my favorite",
        ]
        scores = _bm25_scores("hiking mountains", docs)
        self.assertGreater(scores[0], scores[1])
        self.assertGreater(scores[2], scores[1])

    def test_bm25_empty_query_is_all_zero(self):
        self.assertEqual(_bm25_scores("", ["a b c", "d e f"]), [0.0, 0.0])


class HybridRankTests(unittest.TestCase):
    def _candidates(self):
        return [
            {"id": "1", "content": "my dog is named Rex", "distance": 0.40},
            {"id": "2", "content": "I enjoy playing guitar", "distance": 0.35},
            {"id": "3", "content": "Rex the dog loves the park", "distance": 0.45},
        ]

    def test_relevance_is_normalized_and_present(self):
        ranked = _hybrid_rank("dog", self._candidates(), top_k=3, hybrid=True, alpha=0.7)
        for item in ranked:
            self.assertIn("relevance", item)
            self.assertIn("dense_score", item)
            self.assertIn("lexical_score", item)
            self.assertGreaterEqual(item["relevance"], 0.0)
            self.assertLessEqual(item["relevance"], 1.0)

    def test_lexical_signal_reorders_over_pure_dense(self):
        # By pure dense (distance), id "2" (0.35) would win. But the query "dog"
        # only appears in ids "1" and "3", so hybrid must lift a dog memory to #1.
        ranked = _hybrid_rank("dog", self._candidates(), top_k=3, hybrid=True, alpha=0.5)
        self.assertIn(ranked[0]["id"], {"1", "3"})

    def test_hybrid_off_orders_by_dense_only(self):
        ranked = _hybrid_rank("dog", self._candidates(), top_k=3, hybrid=False, alpha=0.7)
        # Smallest distance (0.35 → id "2") is most relevant with dense only.
        self.assertEqual(ranked[0]["id"], "2")
        self.assertTrue(all(item["lexical_score"] == 0.0 for item in ranked))

    def test_no_lexical_overlap_falls_back_to_dense(self):
        ranked = _hybrid_rank("astronomy", self._candidates(), top_k=3, hybrid=True, alpha=0.7)
        # No query term overlaps any doc → relevance equals dense score.
        for item in ranked:
            self.assertEqual(item["relevance"], item["dense_score"])
        self.assertEqual(ranked[0]["id"], "2")

    def test_truncates_to_top_k(self):
        ranked = _hybrid_rank("dog", self._candidates(), top_k=2, hybrid=True, alpha=0.7)
        self.assertEqual(len(ranked), 2)


class SearchMemoryTests(_RetrieverTestBase):
    def test_scoping_filter_is_applied(self):
        collection = self._install(
            [
                ("1", "hello", {"user_id": "u1", "agent_id": "a1"}, 0.1),
                ("2", "hello", {"user_id": "u2", "agent_id": "a1"}, 0.1),
                ("3", "hello", {"user_id": "u1", "agent_id": "a2"}, 0.1),
            ]
        )
        results = search_memory("user_memory", "hello", "u1", "a1", top_k=5)
        self.assertEqual([r["id"] for r in results], ["1"])
        self.assertEqual(
            collection.last_where, {"$and": [{"user_id": "u1"}, {"agent_id": "a1"}]}
        )

    def test_empty_collection_returns_empty(self):
        self._install([])
        self.assertEqual(search_memory("user_memory", "q", "u1", "a1"), [])

    def test_results_are_scored_and_ranked(self):
        self._install(
            [
                ("1", "coffee in the morning", {"user_id": "u1", "agent_id": "a1"}, 0.5),
                ("2", "I drink coffee daily", {"user_id": "u1", "agent_id": "a1"}, 0.6),
                ("3", "the sky is blue", {"user_id": "u1", "agent_id": "a1"}, 0.55),
            ]
        )
        results = search_memory("user_memory", "coffee", "u1", "a1", top_k=3)
        self.assertTrue(all("relevance" in r for r in results))
        # A coffee memory must rank above the unrelated sky memory.
        self.assertIn(results[0]["id"], {"1", "2"})
        self.assertGreaterEqual(results[0]["relevance"], results[-1]["relevance"])

    def test_hybrid_overfetches_candidate_pool(self):
        collection = self._install(
            [("i", "doc", {"user_id": "u1", "agent_id": "a1"}, 0.1) for i in range(30)]
        )
        search_memory("user_memory", "doc", "u1", "a1", top_k=5, hybrid=True)
        self.assertGreater(collection.last_n_results, 5)

    def test_non_hybrid_fetches_exactly_top_k(self):
        collection = self._install(
            [(str(i), "doc", {"user_id": "u1", "agent_id": "a1"}, 0.1) for i in range(30)]
        )
        search_memory("user_memory", "doc", "u1", "a1", top_k=5, hybrid=False)
        self.assertEqual(collection.last_n_results, 5)


if __name__ == "__main__":
    unittest.main()
