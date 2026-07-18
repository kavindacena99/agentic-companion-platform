"""Tool-use layer for agent-core.

Gives the agent the ability to *act* (set reminders, suggest activities, look up
the user's profile, search the web) — not just talk — via a small typed tool
registry and an OpenAI-style function-calling contract.

Public surface:

* :class:`~tools.base.Tool` / :class:`~tools.base.ToolResult` — the tool contract.
* :class:`~tools.registry.ToolRegistry` and :data:`~tools.registry.default_registry`
  — hold tools, expose their JSON schemas, and dispatch execution by name.

The graph's ``tool_agent`` / ``tool_executor`` nodes are the only callers; tools
themselves never touch LangGraph or the LLM layer.
"""

from tools.base import Tool, ToolResult
from tools.registry import ToolRegistry, build_default_registry, default_registry

__all__ = [
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "default_registry",
    "build_default_registry",
]
