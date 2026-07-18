"""Tests for the agentic router + conditional graph (graph/workflow.py).

Covers the router node, the deterministic crisis fast-path, the conditional-edge
selectors, and an end-to-end assertion that each route class takes a distinct
path — and that crisis never calls the LLM.

    python -m unittest graph.tests_router
"""

import unittest

from graph import workflow as wf
from graph.workflow import (
    RECURSION_LIMIT,
    crisis_response_node,
    initial_state,
    route_after_agent_loader,
    route_after_safety,
    route_from_router,
    router_node,
)


class RouterNodeTests(unittest.TestCase):
    def test_sets_route_and_traces(self):
        state = {**initial_state("u1", "a1", "s", "what is the weather?"), "intent": "question"}
        update = router_node(state)
        self.assertEqual(update["route"], "tool")
        self.assertEqual(update["trace"][-1]["node"], "router")
        self.assertEqual(update["trace"][-1]["decision"], "tool")

    def test_crisis_intent_routes_crisis(self):
        state = {**initial_state("u1", "a1", "s", "i want to die"), "intent": "crisis"}
        self.assertEqual(router_node(state)["route"], "crisis")


class CrisisResponseNodeTests(unittest.TestCase):
    def test_emits_deterministic_message_and_flag(self):
        update = crisis_response_node(initial_state("u1", "a1", "s", "i want to die"))
        self.assertTrue(update["response"])
        self.assertTrue(update["safety_flags"]["crisis"])
        self.assertEqual(update["trace"][-1]["node"], "crisis_response")

    def test_message_is_stable(self):
        a = crisis_response_node(initial_state("u1", "a1", "s", "x"))["response"]
        b = crisis_response_node(initial_state("u2", "a2", "s", "y"))["response"]
        self.assertEqual(a, b)  # deterministic, message-independent


class EdgeSelectorTests(unittest.TestCase):
    def test_router_forks_crisis_vs_proceed(self):
        self.assertEqual(route_from_router({"route": "crisis"}), "crisis")
        self.assertEqual(route_from_router({"route": "direct"}), "proceed")
        self.assertEqual(route_from_router({"route": "retrieve"}), "proceed")

    def test_agent_loader_fork_direct_vs_retrieve(self):
        self.assertEqual(route_after_agent_loader({"route": "direct"}), "direct")
        self.assertEqual(route_after_agent_loader({"route": "retrieve"}), "retrieve")
        self.assertEqual(route_after_agent_loader({"route": "tool"}), "retrieve")

    def test_safety_fork_end_on_crisis(self):
        self.assertEqual(route_after_safety({"route": "crisis"}), "end")
        self.assertEqual(route_after_safety({"route": "direct"}), "continue")


class _GraphHarness(unittest.TestCase):
    """Compiles the real graph with LLM / memory / loader / writeback stubbed."""

    def setUp(self):
        self._saved = {
            "llm_node": wf.llm_node,
            "memory_retriever_node": wf.memory_retriever_node,
            "AgentLoaderService": wf.AgentLoaderService,
            "process_writeback": wf.process_writeback,
        }
        self.visits = {"llm": 0, "memory": 0}

        def spy_llm(state):
            self.visits["llm"] += 1
            return {"response": "LLM_REPLY", "context": dict(state.get("context") or {})}

        real_memory = self._saved["memory_retriever_node"]

        def spy_memory(state):
            self.visits["memory"] += 1
            return real_memory(state)

        class _StubProfile:
            def to_dict(self):
                return {"display_name": "Bff", "persona_prompt": "You are a friend."}

        class _StubLoader:
            def get_agent(self, agent_id):
                return _StubProfile()

        wf.llm_node = spy_llm
        wf.memory_retriever_node = spy_memory
        wf.AgentLoaderService = _StubLoader
        wf.process_writeback = lambda **kwargs: []
        self.graph = wf.build_workflow()

    def tearDown(self):
        for name, value in self._saved.items():
            setattr(wf, name, value)

    def _run(self, message):
        self.visits["llm"] = 0
        self.visits["memory"] = 0
        state = self.graph.invoke(
            initial_state("u1", "best_friend", "sess", message),
            config={"recursion_limit": RECURSION_LIMIT},
        )
        return state


class CrisisFastPathTests(_GraphHarness):
    def test_crisis_never_calls_llm_or_memory(self):
        state = self._run("I want to kill myself")
        self.assertEqual(state["route"], "crisis")
        self.assertEqual(self.visits["llm"], 0)
        self.assertEqual(self.visits["memory"], 0)

    def test_crisis_path_nodes(self):
        state = self._run("I want to kill myself")
        nodes = [entry["node"] for entry in state["trace"]]
        self.assertEqual(nodes, ["input", "intent", "router", "crisis_response"])
        self.assertTrue(state["safety_flags"]["crisis"])


class RoutedPathTests(_GraphHarness):
    def test_direct_skips_retrieval_calls_llm(self):
        state = self._run("good morning friend")
        self.assertEqual(state["route"], "direct")
        self.assertEqual(self.visits["llm"], 1)
        self.assertEqual(self.visits["memory"], 0)

    def test_retrieve_hits_memory_and_llm(self):
        state = self._run("what is the capital of France?")
        self.assertEqual(state["route"], "retrieve")
        self.assertEqual(self.visits["llm"], 1)
        self.assertEqual(self.visits["memory"], 1)

    def test_tool_uses_retrieval_path_for_now(self):
        state = self._run("what is the weather today?")
        self.assertEqual(state["route"], "tool")
        self.assertEqual(self.visits["memory"], 1)


if __name__ == "__main__":
    unittest.main()
