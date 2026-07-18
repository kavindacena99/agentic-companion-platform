"""Tests for the tool-use / ReAct loop (graph/workflow.py).

Covers the tool_agent + tool_executor nodes, their selectors, and an end-to-end
assertion that a 'remind me at 8pm' message invokes a tool and the observation
informs the final reply — with the deterministic safety engine still running
last on the final text only.

    python -m unittest graph.tests_tool_loop
"""

import unittest

from graph import workflow as wf
from graph.state import MAX_TOOL_ITERS
from graph.workflow import (
    RECURSION_LIMIT,
    initial_state,
    route_after_prompt,
    route_after_tool_agent,
    tool_agent_node,
    tool_executor_node,
)


class SelectorTests(unittest.TestCase):
    def test_route_after_prompt_forks_tool(self):
        self.assertEqual(route_after_prompt({"route": "tool"}), "tool")
        self.assertEqual(route_after_prompt({"route": "retrieve"}), "generate")
        self.assertEqual(route_after_prompt({"route": "direct"}), "generate")

    def test_route_after_tool_agent(self):
        self.assertEqual(route_after_tool_agent({"tool_calls": [{"name": "x"}]}), "execute")
        self.assertEqual(route_after_tool_agent({"tool_calls": []}), "done")


class ToolExecutorNodeTests(unittest.TestCase):
    def test_executes_and_records_observation(self):
        state = {
            **initial_state("u1", "a1", "s", "remind me at 8pm to call mom"),
            "tool_calls": [{"id": "c1", "name": "set_reminder", "arguments": {"time": "8pm", "message": "call mom"}}],
        }
        update = tool_executor_node(state)
        self.assertEqual(update["tool_iters"], 1)
        self.assertEqual(update["tool_calls"], [])  # consumed
        self.assertEqual(len(update["tool_results"]), 1)
        result = update["tool_results"][0]
        self.assertTrue(result["ok"])
        self.assertIn("scheduled", result["observation"])

    def test_unknown_tool_records_error_observation(self):
        state = {
            **initial_state("u1", "a1", "s", "hi"),
            "tool_calls": [{"id": "c1", "name": "does_not_exist", "arguments": {}}],
        }
        update = tool_executor_node(state)
        self.assertFalse(update["tool_results"][0]["ok"])
        self.assertIn("unknown tool", update["tool_results"][0]["observation"])


class ToolAgentNodeTests(unittest.TestCase):
    def setUp(self):
        self._saved = (wf.route_tools, wf.route_llm)

    def tearDown(self):
        wf.route_tools, wf.route_llm = self._saved

    def test_tool_calls_are_stored(self):
        wf.route_tools = lambda messages, tools, context=None: {
            "ok": True, "type": "tool_calls",
            "tool_calls": [{"id": "c1", "name": "set_reminder", "arguments": {}}],
        }
        update = tool_agent_node(initial_state("u", "a", "s", "remind me"))
        self.assertEqual(update["tool_calls"][0]["name"], "set_reminder")

    def test_text_is_final(self):
        wf.route_tools = lambda messages, tools, context=None: {"ok": True, "type": "text", "text": "all done"}
        update = tool_agent_node(initial_state("u", "a", "s", "hi"))
        self.assertEqual(update["response"], "all done")
        self.assertEqual(update["tool_calls"], [])

    def test_degrades_when_no_tool_provider(self):
        wf.route_tools = lambda messages, tools, context=None: {"ok": False}
        wf.route_llm = lambda prompt, ctx=None: {"response": "fallback reply", "ok": True}
        update = tool_agent_node(initial_state("u", "a", "s", "hi"))
        self.assertEqual(update["response"], "fallback reply")
        self.assertEqual(update["tool_calls"], [])

    def test_budget_exhausted_forces_final(self):
        # At the cap, the agent must not request more tools — it finalizes.
        called = {"tools": False}

        def route_tools(messages, tools, context=None):
            called["tools"] = True
            return {"ok": True, "type": "tool_calls", "tool_calls": [{"name": "x"}]}

        wf.route_tools = route_tools
        wf.route_llm = lambda prompt, ctx=None: {"response": "final", "ok": True}
        state = {**initial_state("u", "a", "s", "hi"), "tool_iters": MAX_TOOL_ITERS}
        update = tool_agent_node(state)
        self.assertFalse(called["tools"])  # route_tools not consulted past budget
        self.assertEqual(update["response"], "final")


class _ToolGraphHarness(unittest.TestCase):
    """Compiles the real graph with retrieval / critic / loader / writeback stubbed."""

    def setUp(self):
        self._saved = {
            "get_relevant_memories": wf.get_relevant_memories,
            "route_tools": wf.route_tools,
            "route_llm": wf.route_llm,
            "reflect_on_response": wf.reflect_on_response,
            "AgentLoaderService": wf.AgentLoaderService,
            "process_writeback": wf.process_writeback,
            "safety_node": wf.safety_node,
        }
        self.safety = {"ran": False, "draft_seen": None}

        class _StubLoader:
            def get_agent(self, agent_id):
                return type("P", (), {"to_dict": lambda self: {"persona_prompt": "Warm"}})()

        real_safety = self._saved["safety_node"]

        def spy_safety(state):
            self.safety["ran"] = True
            self.safety["draft_seen"] = state.get("response")
            return real_safety(state)

        wf.get_relevant_memories = lambda query, user_id, agent_id, top_k=5: {
            "user_memory": [{"content": "x", "relevance": 0.9}]
        }
        wf.reflect_on_response = lambda **kwargs: {"verdict": "accept", "critique": "", "ok": True}
        wf.AgentLoaderService = _StubLoader
        wf.process_writeback = lambda **kwargs: []
        wf.safety_node = spy_safety

    def tearDown(self):
        for name, value in self._saved.items():
            setattr(wf, name, value)

    def _run(self, route_tools_fn, message):
        wf.route_tools = route_tools_fn
        graph = wf.build_workflow()
        return graph.invoke(
            initial_state("u1", "best_friend", "sess", message),
            config={"recursion_limit": RECURSION_LIMIT},
        )


class ToolLoopAcceptanceTests(_ToolGraphHarness):
    def test_reminder_invokes_tool_and_observation_informs_reply(self):
        calls = {"n": 0}

        def route_tools(messages, tools, context=None):
            calls["n"] += 1
            if calls["n"] == 1:
                return {
                    "ok": True, "type": "tool_calls",
                    "tool_calls": [{"id": "c1", "name": "set_reminder", "arguments": {"time": "8pm", "message": "call mom"}}],
                }
            # The observation must be visible in the scratchpad we get back.
            user_msg = messages[-1]["content"]
            saw = "8:00 pm" in user_msg
            return {"ok": True, "type": "text", "text": f"Reminder set for 8pm. observed={saw}"}

        state = self._run(route_tools, "remind me at 8pm to call mom")
        self.assertEqual(state["route"], "tool")
        # The tool ran and produced an observation.
        self.assertEqual(state["tool_results"][0]["name"], "set_reminder")
        self.assertIn("scheduled", state["tool_results"][0]["observation"])
        # The observation informed the final reply.
        self.assertIn("observed=True", state["response"])

    def test_safety_runs_last_on_final_text(self):
        def route_tools(messages, tools, context=None):
            if not any("TOOL OBSERVATIONS" in m["content"] for m in messages):
                return {"ok": True, "type": "tool_calls", "tool_calls": [{"id": "c1", "name": "suggest_activity", "arguments": {}}]}
            return {"ok": True, "type": "text", "text": "Here is an idea for you."}

        state = self._run(route_tools, "what should i do, i'm bored")
        self.assertTrue(self.safety["ran"])
        self.assertEqual(self.safety["draft_seen"], "Here is an idea for you.")
        nodes = [t["node"] for t in state["trace"]]
        self.assertIn("tool_executor", nodes)

    def test_react_loop_is_bounded(self):
        # A model that always wants a tool must be capped and still answer.
        def route_tools(messages, tools, context=None):
            return {"ok": True, "type": "tool_calls", "tool_calls": [{"id": "c1", "name": "suggest_activity", "arguments": {}}]}

        # route_llm supplies the forced final answer once the budget is hit.
        saved_llm = wf.route_llm
        wf.route_llm = lambda prompt, ctx=None: {"response": "best effort reply", "ok": True}
        try:
            state = self._run(route_tools, "suggest an activity")
        finally:
            wf.route_llm = saved_llm
        self.assertEqual(state["tool_iters"], MAX_TOOL_ITERS)
        self.assertTrue(state["response"])


if __name__ == "__main__":
    unittest.main()
