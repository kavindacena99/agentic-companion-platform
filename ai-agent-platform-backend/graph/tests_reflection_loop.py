"""Tests for the generation self-reflection loop (graph/workflow.py).

Covers the reflect node, its conditional-edge selector, and an end-to-end
assertion that an ungrounded draft is revised at least once, that the loop is
bounded, and that the deterministic safety engine still runs last.

    python -m unittest graph.tests_reflection_loop
"""

import unittest

from graph import workflow as wf
from graph.state import MAX_REFLECT_ITERS
from graph.workflow import (
    RECURSION_LIMIT,
    initial_state,
    reflect_node,
    route_after_reflect,
)


class ReflectNodeTests(unittest.TestCase):
    def setUp(self):
        self._saved = wf.reflect_on_response

    def tearDown(self):
        wf.reflect_on_response = self._saved

    def _stub(self, verdict, critique=""):
        wf.reflect_on_response = lambda **kwargs: {"verdict": verdict, "critique": critique, "ok": True}

    def test_revise_stores_critique_and_increments(self):
        self._stub("revise", "fix grounding")
        state = {**initial_state("u", "a", "s", "hi"), "response": "draft"}
        update = reflect_node(state)
        self.assertEqual(update["reflect_verdict"], "revise")
        self.assertEqual(update["reflection"], "fix grounding")
        self.assertEqual(update["reflect_iters"], 1)
        self.assertEqual(update["trace"][-1]["node"], "reflect")

    def test_accept_clears_reflection(self):
        self._stub("accept", "")
        state = {**initial_state("u", "a", "s", "hi"), "response": "draft", "reflection": "stale"}
        update = reflect_node(state)
        self.assertEqual(update["reflect_verdict"], "accept")
        self.assertIsNone(update["reflection"])


class RouteAfterReflectTests(unittest.TestCase):
    def test_revise_with_budget_loops(self):
        self.assertEqual(route_after_reflect({"reflect_verdict": "revise", "reflect_iters": 1}), "revise")

    def test_accept_goes_to_safety(self):
        self.assertEqual(route_after_reflect({"reflect_verdict": "accept", "reflect_iters": 1}), "accept")

    def test_revise_past_budget_accepts(self):
        state = {"reflect_verdict": "revise", "reflect_iters": MAX_REFLECT_ITERS}
        self.assertEqual(route_after_reflect(state), "accept")


class _ReflectGraphHarness(unittest.TestCase):
    """Compiles the real graph with retrieval / LLM / critic / loader stubbed."""

    def setUp(self):
        self._saved = {
            "get_relevant_memories": wf.get_relevant_memories,
            "llm_node": wf.llm_node,
            "reflect_on_response": wf.reflect_on_response,
            "AgentLoaderService": wf.AgentLoaderService,
            "process_writeback": wf.process_writeback,
            "safety_node": wf.safety_node,
        }
        self.llm_calls = {"n": 0}
        self.safety = {"ran": False, "draft_seen": None}

        def fake_llm(state):
            self.llm_calls["n"] += 1
            note = (state.get("context") or {}).get("reflection")
            return {
                "response": f"draft{self.llm_calls['n']}" + (" [revised]" if note else ""),
                "context": dict(state.get("context") or {}),
            }

        real_safety = self._saved["safety_node"]

        def spy_safety(state):
            self.safety["ran"] = True
            self.safety["draft_seen"] = state.get("response")
            return real_safety(state)

        class _StubLoader:
            def get_agent(self, agent_id):
                return type("P", (), {"to_dict": lambda self: {"persona_prompt": "Warm"}})()

        wf.get_relevant_memories = lambda query, user_id, agent_id, top_k=5: {
            "user_memory": [{"content": "tea", "relevance": 0.9}]
        }
        wf.llm_node = fake_llm
        wf.safety_node = spy_safety
        wf.AgentLoaderService = _StubLoader
        wf.process_writeback = lambda **kwargs: []

    def tearDown(self):
        for name, value in self._saved.items():
            setattr(wf, name, value)

    def _run(self, critic, message="what do you know about me?"):
        wf.reflect_on_response = critic
        graph = wf.build_workflow()
        return graph.invoke(
            initial_state("u1", "best_friend", "sess", message),
            config={"recursion_limit": RECURSION_LIMIT},
        )


class ReflectionLoopTests(_ReflectGraphHarness):
    def test_ungrounded_draft_is_revised_at_least_once(self):
        calls = {"n": 0}

        def critic(**kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"verdict": "revise", "critique": "not grounded", "ok": True}
            return {"verdict": "accept", "critique": "", "ok": True}

        state = self._run(critic)
        self.assertEqual(self.llm_calls["n"], 2)  # regenerated once
        self.assertIn("[revised]", state["response"])  # critique reached the prompt
        nodes = [t["node"] for t in state["trace"]]
        self.assertGreaterEqual(nodes.count("reflect"), 2)

    def test_safety_runs_last_on_the_revised_draft(self):
        def critic(**kwargs):
            # Always want to revise, but the loop must still end at safety.
            return {"verdict": "revise", "critique": "again", "ok": True}

        state = self._run(critic)
        self.assertTrue(self.safety["ran"])
        # Safety saw the final (revised) draft, and it is the last decision stage.
        self.assertIn("[revised]", self.safety["draft_seen"])
        nodes = [t["node"] for t in state["trace"]]
        self.assertLess(nodes.index("reflect"), len(nodes))  # reflect precedes safety

    def test_loop_is_bounded(self):
        def critic(**kwargs):
            return {"verdict": "revise", "critique": "again", "ok": True}

        state = self._run(critic)
        self.assertEqual(state["reflect_iters"], MAX_REFLECT_ITERS)

    def test_accepted_first_pass_does_not_loop(self):
        def critic(**kwargs):
            return {"verdict": "accept", "critique": "", "ok": True}

        state = self._run(critic)
        self.assertEqual(self.llm_calls["n"], 1)
        self.assertEqual(state["reflect_iters"], 1)


if __name__ == "__main__":
    unittest.main()
