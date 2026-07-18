"""Tests for the self-correcting retrieval loop (graph/workflow.py + planner).

Covers the pure query-planner/grader helpers and an end-to-end assertion that a
weak first pass triggers a bounded re-retrieval that improves grounding, and
that a persistently weak query stops at the loop budget and proceeds anyway.

    python -m unittest graph.tests_retrieval_loop
"""

import unittest

from graph import workflow as wf
from graph.state import MAX_RETRIEVE_ITERS
from graph.workflow import (
    RECURSION_LIMIT,
    grade_node,
    initial_state,
    plan_query_node,
    reformulate_node,
    route_after_grade,
)
from memory.query_planner import (
    best_relevance,
    grade_memories,
    plan_query,
    reformulate_query,
)


class PlannerHelperTests(unittest.TestCase):
    def test_plan_query_strips_stopwords(self):
        query = plan_query("what is the capital of France?")
        self.assertNotIn("what", query.split())
        self.assertNotIn("the", query.split())
        self.assertIn("capital", query.split())
        self.assertIn("france", query.split())

    def test_plan_query_falls_back_when_all_stopwords(self):
        self.assertEqual(plan_query("how are you"), "how are you")

    def test_reformulate_broadens_then_enriches(self):
        first = reformulate_query("my dog Rex is sick", iteration=1)
        second = reformulate_query("my dog Rex is sick", iteration=2, emotion="sad")
        self.assertEqual(first, "my dog Rex is sick")  # broaden to full message
        self.assertIn("sad", second.split())           # enrich with affect hint
        self.assertNotEqual(first, second)

    def test_reformulate_ignores_uninformative_hints(self):
        query = reformulate_query("tell me a joke", iteration=2, emotion="neutral", intent="casual")
        self.assertNotIn("neutral", query.split())
        self.assertNotIn("casual", query.split())


class GradeHelperTests(unittest.TestCase):
    def test_empty_is_insufficient(self):
        self.assertEqual(grade_memories([]), "insufficient")

    def test_strong_hit_is_sufficient(self):
        self.assertEqual(grade_memories([{"relevance": 0.8}]), "sufficient")

    def test_all_weak_is_insufficient(self):
        self.assertEqual(grade_memories([{"relevance": 0.1}, {"relevance": 0.2}]), "insufficient")

    def test_best_relevance(self):
        self.assertEqual(best_relevance([{"relevance": 0.2}, {"relevance": 0.7}]), 0.7)
        self.assertEqual(best_relevance([]), 0.0)


class GradeNodeAndSelectorTests(unittest.TestCase):
    def test_grade_node_sets_grade_and_trace(self):
        state = {**initial_state("u", "a", "s", "hi"), "retrieved": [{"relevance": 0.9}]}
        update = grade_node(state)
        self.assertEqual(update["relevance_grade"], "sufficient")
        self.assertEqual(update["trace"][-1]["node"], "grade")

    def test_selector_loops_when_insufficient_with_budget(self):
        state = {"relevance_grade": "insufficient", "retrieve_iters": 1}
        self.assertEqual(route_after_grade(state), "reformulate")

    def test_selector_generates_when_sufficient(self):
        state = {"relevance_grade": "sufficient", "retrieve_iters": 1}
        self.assertEqual(route_after_grade(state), "generate")

    def test_selector_generates_when_budget_exhausted(self):
        state = {"relevance_grade": "insufficient", "retrieve_iters": MAX_RETRIEVE_ITERS}
        self.assertEqual(route_after_grade(state), "generate")

    def test_plan_and_reformulate_nodes_set_search_query(self):
        planned = plan_query_node(initial_state("u", "a", "s", "where is the library?"))
        self.assertTrue(planned["search_query"])
        ref = reformulate_node({**initial_state("u", "a", "s", "where is the library?"), "retrieve_iters": 1})
        self.assertTrue(ref["search_query"])


class _LoopHarness(unittest.TestCase):
    """Compiles the real graph with retrieval / LLM / loader / writeback stubbed."""

    def setUp(self):
        self._saved = {
            "get_relevant_memories": wf.get_relevant_memories,
            "llm_node": wf.llm_node,
            "AgentLoaderService": wf.AgentLoaderService,
            "process_writeback": wf.process_writeback,
        }

        class _StubLoader:
            def get_agent(self, agent_id):
                return type("P", (), {"to_dict": lambda self: {"persona_prompt": "p"}})()

        wf.llm_node = lambda s: {"response": "REPLY", "context": dict(s.get("context") or {})}
        wf.AgentLoaderService = _StubLoader
        wf.process_writeback = lambda **kwargs: []

    def tearDown(self):
        for name, value in self._saved.items():
            setattr(wf, name, value)

    def _run_with(self, retrieval_fn, message="what is the capital of France?"):
        wf.get_relevant_memories = retrieval_fn
        graph = wf.build_workflow()
        return graph.invoke(
            initial_state("u1", "best_friend", "sess", message),
            config={"recursion_limit": RECURSION_LIMIT},
        )


class SelfCorrectionTests(_LoopHarness):
    def test_weak_first_pass_reretrieves_and_improves_grounding(self):
        self.calls = {"n": 0}

        def retrieval(query, user_id, agent_id, top_k=5):
            self.calls["n"] += 1
            if self.calls["n"] == 1:
                return {"user_memory": [{"content": "noise", "relevance": 0.1}]}
            return {"user_memory": [{"content": "Paris", "relevance": 0.85}]}

        state = self._run_with(retrieval)
        self.assertEqual(state["route"], "retrieve")
        self.assertEqual(state["relevance_grade"], "sufficient")
        self.assertEqual(self.calls["n"], 2)  # one re-retrieval
        # Grounding improved from the weak first pass to a strong final pass.
        self.assertGreaterEqual(best_relevance(state["retrieved"]), 0.85)
        nodes = [t["node"] for t in state["trace"]]
        self.assertIn("reformulate", nodes)

    def test_persistently_weak_query_is_bounded_then_proceeds(self):
        self.calls = {"n": 0}

        def retrieval(query, user_id, agent_id, top_k=5):
            self.calls["n"] += 1
            return {"user_memory": [{"content": "weak", "relevance": 0.05}]}

        state = self._run_with(retrieval)
        self.assertEqual(state["retrieve_iters"], MAX_RETRIEVE_ITERS)
        self.assertEqual(self.calls["n"], MAX_RETRIEVE_ITERS)
        self.assertEqual(state["relevance_grade"], "insufficient")
        # Best-effort: a response is still produced despite weak grounding.
        self.assertTrue(state["response"])

    def test_strong_first_pass_does_not_loop(self):
        self.calls = {"n": 0}

        def retrieval(query, user_id, agent_id, top_k=5):
            self.calls["n"] += 1
            return {"user_memory": [{"content": "Paris", "relevance": 0.9}]}

        state = self._run_with(retrieval)
        self.assertEqual(self.calls["n"], 1)
        self.assertEqual(state["retrieve_iters"], 1)
        nodes = [t["node"] for t in state["trace"]]
        self.assertNotIn("reformulate", nodes)


if __name__ == "__main__":
    unittest.main()
