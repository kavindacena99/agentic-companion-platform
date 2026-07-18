"""Tool registry — holds tools, exposes their schemas, dispatches execution.

The registry is the single boundary the graph talks to: it turns the set of
registered :class:`~tools.base.Tool` objects into the JSON schemas the model
needs (``schemas()``) and executes a model-requested call by name
(``execute()``), always returning a normalized :class:`~tools.base.ToolResult`
— an unknown tool name yields an error observation rather than an exception.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from tools.base import Tool, ToolResult
from tools.builtin import (
    FetchUserProfileTool,
    SearchWebTool,
    SetReminderTool,
    SuggestActivityTool,
)

logger = logging.getLogger("agent_core")


class ToolRegistry:
    """A name-indexed collection of tools."""

    def __init__(self, tools: List[Tool] | None = None):
        self._tools: Dict[str, Tool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.warning("Tool '%s' is already registered; overwriting.", tool.name)
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return list(self._tools)

    def __len__(self) -> int:
        return len(self._tools)

    def schemas(self) -> List[Dict[str, Any]]:
        """OpenAI-style function-tool schemas for every registered tool."""
        return [tool.to_schema() for tool in self._tools.values()]

    def execute(
        self, name: str, arguments: Dict[str, Any], context: Dict[str, Any] | None = None
    ) -> ToolResult:
        """Dispatch ``name`` with ``arguments``; unknown names fail gracefully."""
        tool = self._tools.get(name)
        if tool is None:
            logger.warning("Requested unknown tool '%s'.", name)
            return ToolResult(ok=False, error=f"unknown tool '{name}'")
        return tool.execute(arguments, context or {})


def build_default_registry() -> ToolRegistry:
    """Construct a registry with the built-in tools registered."""
    return ToolRegistry(
        [
            SetReminderTool(),
            SuggestActivityTool(),
            FetchUserProfileTool(),
            SearchWebTool(),
        ]
    )


# Shared default registry used by the graph.
default_registry = build_default_registry()
