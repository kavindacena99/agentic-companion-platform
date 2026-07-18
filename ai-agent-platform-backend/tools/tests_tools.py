"""Tests for the tool-use layer (tools/).

Runs standalone (no network — HTTP is injected):

    python -m unittest tools.tests_tools
"""

import unittest

from tools.base import Tool, ToolResult
from tools.builtin import (
    FetchUserProfileTool,
    SearchWebTool,
    SetReminderTool,
    SuggestActivityTool,
)
from tools.registry import ToolRegistry, build_default_registry


class ToolResultTests(unittest.TestCase):
    def test_ok_observation_renders_data(self):
        self.assertEqual(ToolResult(ok=True, data={"a": 1, "b": "x"}).to_observation(), "a=1; b=x")

    def test_ok_empty_observation(self):
        self.assertEqual(ToolResult(ok=True).to_observation(), "ok")

    def test_error_observation(self):
        self.assertEqual(ToolResult(ok=False, error="nope").to_observation(), "error: nope")


class ToolBaseTests(unittest.TestCase):
    def test_execute_never_raises(self):
        class Boom(Tool):
            name = "boom"

            def run(self, arguments, context):
                raise ValueError("kaboom")

        result = Boom().execute({}, {})
        self.assertFalse(result.ok)
        self.assertIn("kaboom", result.error)

    def test_schema_shape(self):
        schema = SetReminderTool().to_schema()
        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], "set_reminder")
        self.assertIn("time", schema["function"]["parameters"]["properties"])


class SetReminderTests(unittest.TestCase):
    def test_schedules_and_normalizes_time(self):
        result = SetReminderTool().run({"time": "8pm", "message": "call mom"}, {"user_id": "u1"})
        self.assertTrue(result.ok)
        self.assertEqual(result.data["status"], "scheduled")
        self.assertEqual(result.data["time"], "8:00 pm")
        self.assertEqual(result.data["message"], "call mom")

    def test_missing_argument(self):
        result = SetReminderTool().run({"time": "8pm"}, {})
        self.assertFalse(result.ok)
        self.assertIn("message", result.error)


class SuggestActivityTests(unittest.TestCase):
    def test_mood_specific(self):
        result = SuggestActivityTool().run({"mood": "anxious"}, {})
        self.assertTrue(result.ok)
        self.assertIn("breathing", result.data["suggestion"])

    def test_falls_back_to_context_emotion(self):
        result = SuggestActivityTool().run({}, {"emotion": "bored"})
        self.assertEqual(result.data["mood"], "bored")

    def test_default_when_unknown(self):
        result = SuggestActivityTool().run({"mood": "zzz"}, {})
        self.assertTrue(result.ok)
        self.assertEqual(result.data["mood"], "zzz")


class FetchUserProfileTests(unittest.TestCase):
    def _resp(self, status, payload=None):
        return type("R", (), {"status_code": status, "json": lambda self: payload or {}})()

    def test_not_configured_without_base_url(self):
        tool = FetchUserProfileTool(base_url="")
        result = tool.run({}, {"user_id": "u1"})
        self.assertFalse(result.ok)
        self.assertIn("not configured", result.error)

    def test_returns_profile_fields(self):
        captured = {}

        def http_get(url, headers, params, timeout):
            captured["url"] = url
            captured["params"] = params
            return self._resp(200, {"display_name": "Sam", "timezone": "UTC", "secret": "x"})

        tool = FetchUserProfileTool(base_url="http://backend", http_get=http_get)
        result = tool.run({}, {"user_id": "u1"})
        self.assertTrue(result.ok)
        self.assertEqual(result.data, {"display_name": "Sam", "timezone": "UTC"})  # 'secret' dropped
        self.assertEqual(captured["params"], {"user_id": "u1"})

    def test_http_error_degrades(self):
        tool = FetchUserProfileTool(base_url="http://backend", http_get=lambda url, **k: self._resp(404))
        result = tool.run({}, {"user_id": "u1"})
        self.assertFalse(result.ok)
        self.assertIn("404", result.error)

    def test_execute_catches_exception(self):
        def boom(url, headers, params, timeout):
            raise RuntimeError("connection reset")

        tool = FetchUserProfileTool(base_url="http://backend", http_get=boom)
        result = tool.execute({}, {"user_id": "u1"})  # execute() is the safe wrapper
        self.assertFalse(result.ok)
        self.assertIn("connection reset", result.error)


class SearchWebTests(unittest.TestCase):
    def test_guarded_off_by_default(self):
        result = SearchWebTool().run({"query": "news"}, {})
        self.assertFalse(result.ok)
        self.assertIn("not configured", result.error)

    def test_uses_injected_backend(self):
        tool = SearchWebTool(search_fn=lambda q: [f"result for {q}"])
        result = tool.run({"query": "python"}, {})
        self.assertTrue(result.ok)
        self.assertEqual(result.data["results"], ["result for python"])

    def test_missing_query(self):
        result = SearchWebTool(search_fn=lambda q: []).run({}, {})
        self.assertFalse(result.ok)


class RegistryTests(unittest.TestCase):
    def test_default_registry_has_all_builtins(self):
        registry = build_default_registry()
        self.assertEqual(
            set(registry.names()),
            {"set_reminder", "suggest_activity", "fetch_user_profile", "search_web"},
        )
        self.assertEqual(len(registry.schemas()), 4)

    def test_execute_dispatches(self):
        registry = build_default_registry()
        result = registry.execute("set_reminder", {"time": "9am", "message": "gym"}, {"user_id": "u"})
        self.assertTrue(result.ok)

    def test_unknown_tool_is_graceful(self):
        result = ToolRegistry().execute("nope", {}, {})
        self.assertFalse(result.ok)
        self.assertIn("unknown tool", result.error)


if __name__ == "__main__":
    unittest.main()
