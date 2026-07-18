"""Tests for the route selector (services/classifiers/route_selector.py).

Runs standalone (no LangGraph / network needed):

    python -m unittest services.classifiers.tests_route_selector
"""

import unittest

from services.classifiers.route_selector import (
    ROUTE_CRISIS,
    ROUTE_DIRECT,
    ROUTE_RETRIEVE,
    ROUTE_TOOL,
    ROUTE_TYPES,
    select_route,
)


class SelectRouteTests(unittest.TestCase):
    def test_crisis_intent_always_wins(self):
        # Even if a tool keyword is present, crisis takes precedence.
        self.assertEqual(select_route("crisis", "what is the weather"), ROUTE_CRISIS)
        self.assertEqual(select_route("crisis", "i want to end my life"), ROUTE_CRISIS)

    def test_casual_routes_direct(self):
        self.assertEqual(select_route("casual", "haha good morning"), ROUTE_DIRECT)

    def test_question_routes_retrieve(self):
        self.assertEqual(select_route("question", "what is the capital of France?"), ROUTE_RETRIEVE)

    def test_emotional_routes_retrieve(self):
        self.assertEqual(select_route("emotional", "i feel so lonely"), ROUTE_RETRIEVE)

    def test_tool_keywords_route_tool(self):
        for msg in (
            "what is the weather today?",
            "what time is it in Tokyo?",
            "search the web for me",
            "give me the latest news",
        ):
            self.assertEqual(select_route("question", msg), ROUTE_TOOL, msg)

    def test_tool_beats_retrieve_for_non_crisis(self):
        # A question that needs live data goes to tool, not plain retrieve.
        self.assertEqual(select_route("question", "what's the weather?"), ROUTE_TOOL)

    def test_all_routes_are_declared(self):
        for route in (ROUTE_CRISIS, ROUTE_DIRECT, ROUTE_RETRIEVE, ROUTE_TOOL):
            self.assertIn(route, ROUTE_TYPES)

    def test_empty_message_defaults_direct(self):
        self.assertEqual(select_route("casual", ""), ROUTE_DIRECT)


if __name__ == "__main__":
    unittest.main()
