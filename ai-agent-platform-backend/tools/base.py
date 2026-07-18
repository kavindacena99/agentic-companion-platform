"""Tool contract: a typed, self-describing action the agent can invoke.

Every tool declares a ``name``, a natural-language ``description`` (what the
model reads to decide when to call it), and a JSON-schema ``parameters`` object
(the OpenAI function-calling ``parameters`` shape). Execution goes through
:meth:`Tool.run`, which must **never raise** — it always returns a
:class:`ToolResult` so a misbehaving tool degrades into an observation instead
of crashing the reasoning graph.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict

logger = logging.getLogger("agent_core")


@dataclass
class ToolResult:
    """Normalized outcome of a tool invocation.

    ``ok`` marks success; ``data`` carries structured payload on success and
    ``error`` a short human-readable reason on failure. :meth:`to_observation`
    renders the compact text the model sees on the next ReAct turn.
    """

    ok: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def to_observation(self) -> str:
        if self.ok:
            if not self.data:
                return "ok"
            return "; ".join(f"{key}={value}" for key, value in self.data.items())
        return f"error: {self.error or 'tool failed'}"

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "data": self.data, "error": self.error}


class Tool(ABC):
    """Abstract base for every tool the agent can call."""

    #: Unique function name exposed to the model (snake_case).
    name: str = "tool"
    #: What the tool does — read by the model to decide when to call it.
    description: str = ""
    #: JSON-schema object describing the arguments (OpenAI ``parameters`` shape).
    parameters: Dict[str, Any] = {"type": "object", "properties": {}}

    @abstractmethod
    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute the tool. Implementations must not raise — return ToolResult."""
        raise NotImplementedError

    def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Run with a safety net so a buggy tool can never crash the graph."""
        try:
            return self.run(arguments or {}, context or {})
        except Exception as exc:  # noqa: BLE001 — tools must degrade, never crash
            logger.warning("Tool '%s' raised, returning error observation: %s", self.name, exc)
            return ToolResult(ok=False, error=f"{type(exc).__name__}: {exc}")

    def to_schema(self) -> Dict[str, Any]:
        """Return the OpenAI-style function tool schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def _require(self, arguments: Dict[str, Any], *names: str) -> str:
        """Return the name of the first missing required argument ('' if none)."""
        for name in names:
            value = arguments.get(name)
            if value is None or (isinstance(value, str) and not value.strip()):
                return name
        return ""
