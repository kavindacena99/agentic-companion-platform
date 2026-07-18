"""Tests for provider tool-calling + the tool router (llm/).

Runs standalone (no network — the OpenAI client is faked):

    python -m unittest llm.tests_tool_calling
"""

import unittest

from llm.gemini_provider import GeminiProvider
from llm.llm_router import LLMRouter
from llm.openai_provider import OpenAIProvider


# --- Fake OpenAI SDK objects -------------------------------------------------
class _FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, id, name, arguments):
        self.id = id
        self.function = _FakeFunction(name, arguments)


class _FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self):
        return {"role": "assistant", "content": self.content, "tool_calls": bool(self.tool_calls)}


class _FakeCompletions:
    def __init__(self, message):
        self._message = message
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return type("Resp", (), {"choices": [type("C", (), {"message": self._message})()]})()


class _FakeClient:
    def __init__(self, message):
        self.chat = type("Chat", (), {"completions": _FakeCompletions(message)})()


def _openai_with(message):
    provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
    provider._client = _FakeClient(message)
    return provider


class OpenAIToolCallingTests(unittest.TestCase):
    def test_supports_tools_when_available(self):
        self.assertTrue(_openai_with(_FakeMessage(content="hi")).supports_tools())

    def test_returns_normalized_tool_calls(self):
        message = _FakeMessage(tool_calls=[_FakeToolCall("c1", "set_reminder", '{"time":"8pm"}')])
        result = _openai_with(message).generate_with_tools([{"role": "user", "content": "x"}], [])
        self.assertEqual(result["type"], "tool_calls")
        self.assertEqual(result["tool_calls"][0]["name"], "set_reminder")
        self.assertEqual(result["tool_calls"][0]["arguments"], {"time": "8pm"})  # parsed to dict
        self.assertEqual(result["tool_calls"][0]["id"], "c1")

    def test_bad_json_arguments_degrade_to_empty(self):
        message = _FakeMessage(tool_calls=[_FakeToolCall("c1", "t", "{not json}")])
        result = _openai_with(message).generate_with_tools([], [])
        self.assertEqual(result["tool_calls"][0]["arguments"], {})

    def test_returns_text_when_no_tool_calls(self):
        result = _openai_with(_FakeMessage(content="final answer")).generate_with_tools([], [])
        self.assertEqual(result["type"], "text")
        self.assertEqual(result["text"], "final answer")

    def test_passes_tools_and_tool_choice(self):
        provider = _openai_with(_FakeMessage(content="hi"))
        provider.generate_with_tools([{"role": "user", "content": "x"}], [{"type": "function"}])
        kwargs = provider._client.chat.completions.last_kwargs
        self.assertEqual(kwargs["tools"], [{"type": "function"}])
        self.assertEqual(kwargs["tool_choice"], "auto")


class GeminiGuardTests(unittest.TestCase):
    def test_gemini_does_not_support_tools(self):
        self.assertFalse(GeminiProvider(api_key="k").supports_tools())


class RouteToolsTests(unittest.TestCase):
    def test_selects_tool_capable_provider(self):
        message = _FakeMessage(content="answer")
        router = LLMRouter(providers={"openai": _openai_with(message), "gemini": GeminiProvider(api_key="")})
        result = router.route_tools([{"role": "user", "content": "hi"}], [])
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["type"], "text")

    def test_skips_providers_without_tool_support(self):
        # Only Gemini (no tool support) present → no capable provider → ok False.
        router = LLMRouter(providers={"gemini": GeminiProvider(api_key="key-but-no-tools")})
        result = router.route_tools([], [])
        self.assertFalse(result["ok"])

    def test_degrades_when_provider_raises(self):
        class Boom(OpenAIProvider):
            def supports_tools(self):
                return True

            def generate_with_tools(self, messages, tools, **kwargs):
                raise RuntimeError("api down")

        router = LLMRouter(providers={"openai": Boom(api_key="k")})
        result = router.route_tools([], [])
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
