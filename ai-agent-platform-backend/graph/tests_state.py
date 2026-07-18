"""Tests for the agentic control scaffolding (graph/state.py).

Runs standalone (no LangGraph / network needed):

    python -m unittest graph.tests_state

Covers the loop-bound constants, the new control fields, and the ``append_trace``
decision-recording helper.
"""

import unittest

from graph.state import (
    MAX_REFLECT_ITERS,
    MAX_RETRIEVE_ITERS,
    append_trace,
)

# Fields the agentic control layer must add to AgentState / initial_state.
_CONTROL_FIELDS = {
    "route",
    "search_query",
    "retrieved",
    "relevance_grade",
    "retrieve_iters",
    "tool_calls",
    "tool_results",
    "reflection",
    "reflect_iters",
    "trace",
}


class LoopBoundTests(unittest.TestCase):
    def test_bounds_are_positive_ints(self):
        self.assertIsInstance(MAX_RETRIEVE_ITERS, int)
        self.assertIsInstance(MAX_REFLECT_ITERS, int)
        self.assertGreater(MAX_RETRIEVE_ITERS, 0)
        self.assertGreater(MAX_REFLECT_ITERS, 0)


class AppendTraceTests(unittest.TestCase):
    def test_appends_entry_with_metadata(self):
        trace = append_trace({}, "grade", "insufficient", score=0.2)
        self.assertEqual(len(trace), 1)
        entry = trace[0]
        self.assertEqual(entry["step"], 1)
        self.assertEqual(entry["node"], "grade")
        self.assertEqual(entry["decision"], "insufficient")
        self.assertEqual(entry["details"], {"score": 0.2})
        self.assertIn("at", entry)

    def test_details_omitted_when_empty(self):
        entry = append_trace({}, "input", "accepted")[0]
        self.assertNotIn("details", entry)

    def test_steps_increment_across_calls(self):
        first = append_trace({}, "input", "accepted")
        second = append_trace({"trace": first}, "intent", "casual")
        self.assertEqual([e["step"] for e in second], [1, 2])
        self.assertEqual([e["node"] for e in second], ["input", "intent"])

    def test_does_not_mutate_input_state(self):
        state = {"trace": []}
        append_trace(state, "input", "accepted")
        # Helper returns a new list; the caller's state is untouched until it
        # merges the returned value back in.
        self.assertEqual(state["trace"], [])

    def test_handles_missing_trace_key(self):
        # A fresh state may not carry a trace yet; the helper tolerates it.
        self.assertEqual(len(append_trace({}, "input", "accepted")), 1)


class InitialStateTests(unittest.TestCase):
    """initial_state lives in graph.workflow (pulls in LangGraph); skip if absent."""

    def setUp(self):
        try:
            from graph.workflow import initial_state
        except Exception as exc:  # pragma: no cover - env without langgraph
            self.skipTest(f"graph.workflow unavailable: {exc}")
        self.state = initial_state("u1", "a1", "sess", "hi")

    def test_control_fields_present(self):
        self.assertTrue(_CONTROL_FIELDS.issubset(self.state.keys()))

    def test_counters_start_at_zero(self):
        self.assertEqual(self.state["retrieve_iters"], 0)
        self.assertEqual(self.state["reflect_iters"], 0)

    def test_collections_start_empty(self):
        for field in ("retrieved", "tool_calls", "tool_results", "trace"):
            self.assertEqual(self.state[field], [])

    def test_scalars_start_none(self):
        for field in ("route", "search_query", "relevance_grade", "reflection"):
            self.assertIsNone(self.state[field])


if __name__ == "__main__":
    unittest.main()
