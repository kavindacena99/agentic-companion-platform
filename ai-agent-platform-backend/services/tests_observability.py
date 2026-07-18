"""Tests for observability + chat-service trace exposure.

Standalone (no graph / network — run_workflow is stubbed):

    python -m unittest services.tests_observability
"""

import os
import unittest

import services.chat_service as chat_service
from services.observability import summarize_run, trace_summary
from services.schemas.message import ChatMessage


def _sample_state():
    return {
        "route": "tool",
        "intent": "question",
        "emotion": "curious",
        "relevance_grade": "sufficient",
        "reflect_verdict": "accept",
        "retrieve_iters": 2,
        "reflect_iters": 1,
        "tool_iters": 1,
        "tool_results": [{"name": "set_reminder", "ok": True}],
        "context": {"llm_provider": "openai", "llm_ok": True},
        "safety_flags": {"crisis": False, "response_rewritten": True, "rewrite_reason": "manipulation"},
        "trace": [{"node": "router", "decision": "tool"}, {"node": "safety", "decision": "manipulation"}],
        "response": "hi",
        "emotion_out": None,
    }


class SummarizeRunTests(unittest.TestCase):
    def test_reports_route_loops_tools_provider(self):
        metrics = summarize_run(_sample_state(), latency_ms=123.456)
        self.assertEqual(metrics["route"], "tool")
        self.assertEqual(metrics["loops"], {"retrieve_iters": 2, "reflect_iters": 1, "tool_iters": 1})
        self.assertEqual(metrics["tools_used"], ["set_reminder"])
        self.assertEqual(metrics["provider"], "openai")
        self.assertEqual(metrics["latency_ms"], 123.5)  # rounded to 1 dp
        self.assertEqual(metrics["trace_steps"], 2)

    def test_reports_safety_summary(self):
        metrics = summarize_run(_sample_state())
        self.assertTrue(metrics["safety"]["response_rewritten"])
        self.assertEqual(metrics["safety"]["rewrite_reason"], "manipulation")
        self.assertNotIn("latency_ms", metrics)  # omitted when not provided

    def test_handles_empty_state(self):
        metrics = summarize_run({})
        self.assertIsNone(metrics["route"])
        self.assertEqual(metrics["loops"]["tool_iters"], 0)
        self.assertEqual(metrics["tools_used"], [])

    def test_trace_summary_labels(self):
        labels = trace_summary([{"node": "router", "decision": "tool"}, {"node": "grade", "decision": "sufficient"}])
        self.assertEqual(labels, ["router:tool", "grade:sufficient"])


class ProcessChatTraceExposureTests(unittest.TestCase):
    def setUp(self):
        self._saved_run = chat_service.run_workflow
        self._saved_env = os.environ.get("AGENT_CORE_EXPOSE_TRACE")
        chat_service.run_workflow = lambda **kwargs: {
            **_sample_state(),
            "response": "hello there",
            "intent": "question",
            "emotion": "curious",
        }

    def tearDown(self):
        chat_service.run_workflow = self._saved_run
        if self._saved_env is None:
            os.environ.pop("AGENT_CORE_EXPOSE_TRACE", None)
        else:
            os.environ["AGENT_CORE_EXPOSE_TRACE"] = self._saved_env

    def _msg(self, debug):
        return ChatMessage(user_id="u", agent_id="a", session_id="s", message="hi", debug=debug)

    def test_debug_false_hides_trace(self):
        result = chat_service.process_chat(self._msg(False))
        self.assertEqual(set(result), {"response", "emotion", "intent"})

    def test_debug_true_exposes_trace_and_metrics(self):
        os.environ["AGENT_CORE_EXPOSE_TRACE"] = "true"
        result = chat_service.process_chat(self._msg(True))
        self.assertIn("trace", result)
        self.assertIn("metrics", result)
        self.assertEqual(result["metrics"]["route"], "tool")

    def test_env_can_disable_trace_exposure(self):
        os.environ["AGENT_CORE_EXPOSE_TRACE"] = "false"
        result = chat_service.process_chat(self._msg(True))
        self.assertNotIn("trace", result)


if __name__ == "__main__":
    unittest.main()
