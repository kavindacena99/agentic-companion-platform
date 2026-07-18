"""Tests for the reflection critic helper (llm/reflection.py).

Runs standalone (no network — the LLM router is injected as a fake):

    python -m unittest llm.tests_reflection
"""

import unittest

from llm.reflection import (
    ACCEPT,
    REVISE,
    _parse_reflection,
    build_reflection_prompt,
    reflect_on_response,
)


def _router_returning(text, ok=True):
    def router(prompt, context=None):
        router.last_prompt = prompt
        router.last_context = context
        return {"provider": "gemini", "response": text, "ok": ok}

    return router


class ParseTests(unittest.TestCase):
    def test_parses_accept(self):
        self.assertEqual(_parse_reflection("VERDICT: ACCEPT\nREASON: fine")["verdict"], ACCEPT)

    def test_parses_revise_and_reason(self):
        parsed = _parse_reflection("VERDICT: REVISE\nREASON: invented a fact")
        self.assertEqual(parsed["verdict"], REVISE)
        self.assertEqual(parsed["critique"], "invented a fact")

    def test_defaults_to_accept_when_unparseable(self):
        self.assertEqual(_parse_reflection("hello there")["verdict"], ACCEPT)

    def test_bare_revise_word_is_detected(self):
        self.assertEqual(_parse_reflection("I would revise this")["verdict"], REVISE)


class ReflectOnResponseTests(unittest.TestCase):
    def test_uses_low_cost_provider(self):
        router = _router_returning("VERDICT: ACCEPT")
        reflect_on_response("hi", "hello!", [], "persona", "happy", router=router)
        self.assertEqual(router.last_context["quality"], "low")

    def test_revise_verdict_passes_through(self):
        router = _router_returning("VERDICT: REVISE\nREASON: not grounded")
        result = reflect_on_response("hi", "draft", [{"content": "x"}], "p", router=router)
        self.assertEqual(result["verdict"], REVISE)
        self.assertEqual(result["critique"], "not grounded")
        self.assertTrue(result["ok"])

    def test_empty_draft_fails_open(self):
        result = reflect_on_response("hi", "   ", [], "p", router=_router_returning("REVISE"))
        self.assertEqual(result["verdict"], ACCEPT)
        self.assertFalse(result["ok"])

    def test_provider_unavailable_fails_open(self):
        router = _router_returning("VERDICT: REVISE", ok=False)
        result = reflect_on_response("hi", "draft", [], "p", router=router)
        self.assertEqual(result["verdict"], ACCEPT)
        self.assertFalse(result["ok"])

    def test_router_exception_fails_open(self):
        def boom(prompt, context=None):
            raise RuntimeError("network down")

        result = reflect_on_response("hi", "draft", [], "p", router=boom)
        self.assertEqual(result["verdict"], ACCEPT)
        self.assertFalse(result["ok"])

    def test_prompt_includes_memories_and_draft(self):
        prompt = build_reflection_prompt(
            "how am I?", "You love tea", [{"content": "likes tea"}], "Warm friend", "curious"
        )
        self.assertIn("likes tea", prompt)
        self.assertIn("You love tea", prompt)
        self.assertIn("Warm friend", prompt)


if __name__ == "__main__":
    unittest.main()
