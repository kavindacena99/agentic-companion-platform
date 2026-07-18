"""Evaluation suite — asserts routing, retrieval relevance, groundedness, safety.

Runs the real compiled reasoning graph over fixture conversations with all
external dependencies stubbed (see ``harness.py``), so it is deterministic and
CI-friendly (no network / API keys / database).

    python -m unittest tests.eval.test_eval
"""

import unittest

from services.observability import summarize_run
from tests.eval import fixtures
from tests.eval.harness import run_turn


class RoutingEval(unittest.TestCase):
    """Each message class takes its expected route."""

    def test_routing_matches_expectation(self):
        for case in fixtures.ROUTING_CASES:
            with self.subTest(case=case["name"]):
                result = run_turn(case["message"])
                self.assertEqual(result.route, case["expect_route"], case["message"])


class RetrievalRelevanceEval(unittest.TestCase):
    """A relevant memory grades sufficient and drives grounding."""

    def test_relevant_memory_grades_sufficient(self):
        for case in fixtures.RETRIEVAL_CASES:
            with self.subTest(case=case["name"]):
                result = run_turn(case["message"], memories=case["memories"])
                self.assertEqual(result.state.get("relevance_grade"), case["expect_grade"])
                best = max((m.get("relevance", 0.0) for m in result.retrieved), default=0.0)
                self.assertGreaterEqual(best, case["min_best_relevance"])
                self.assertTrue(result.visited("retrieve"))


class GroundednessEval(unittest.TestCase):
    """The reply reflects the retrieved memory (not a hallucination)."""

    def test_reply_is_grounded_in_memory(self):
        memories = {"user_memory": [{"content": "User is training for a marathon", "relevance": 0.9}]}
        result = run_turn("what am I training for?", memories=memories)
        self.assertIn("marathon", result.response.lower())

    def test_ungrounded_draft_triggers_revision(self):
        # Critic says revise once → the retrieval+generation loop runs again.
        calls = {"n": 0}

        def critic(**kwargs):
            calls["n"] += 1
            return {"verdict": "revise" if calls["n"] == 1 else "accept", "critique": "ground it", "ok": True}

        result = run_turn(
            "what do you know about me?",
            memories={"user_memory": [{"content": "User likes jazz", "relevance": 0.9}]},
            reflect_script=critic,
        )
        self.assertGreaterEqual(result.trace_labels.count("reflect:revise"), 1)


class SafetyEval(unittest.TestCase):
    """Crisis never calls the LLM; unsafe drafts are rewritten; safety runs last."""

    def test_crisis_and_unsafe_cases(self):
        for case in fixtures.SAFETY_CASES:
            with self.subTest(case=case["name"]):
                result = run_turn(case["message"], llm_text=case.get("llm_text"))
                if case.get("expect_crisis"):
                    self.assertTrue(result.safety_flags.get("crisis"))
                if case.get("expect_llm_call") is False:
                    # Crisis fast-path skips generation entirely.
                    self.assertFalse(result.visited("llm"))
                    self.assertFalse(result.visited("tool_agent"))
                if case.get("expect_rewritten"):
                    self.assertTrue(result.safety_flags.get("response_rewritten"))

    def test_safety_is_always_the_final_decision(self):
        # For any non-crisis generation path, safety must appear after reflect.
        result = run_turn("what is the capital of France?")
        labels = [e["node"] for e in result.trace]
        self.assertIn("safety", labels)
        self.assertGreater(labels.index("safety"), labels.index("reflect"))


class MetricsEval(unittest.TestCase):
    """The run exposes measurable metrics (loops, tools, provider, trace size)."""

    def test_summarize_run_reports_metrics(self):
        result = run_turn("remind me at 8pm to call mom")
        metrics = summarize_run(result.state, latency_ms=12.3)
        self.assertEqual(metrics["route"], "tool")
        self.assertIn("retrieve_iters", metrics["loops"])
        self.assertEqual(metrics["latency_ms"], 12.3)
        self.assertGreater(metrics["trace_steps"], 0)


if __name__ == "__main__":
    unittest.main()
