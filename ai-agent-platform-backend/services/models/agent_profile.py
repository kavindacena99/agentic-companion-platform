"""Unified, in-memory representation of a fully-loaded agent.

An ``AgentProfile`` is the merge of three independent sources:

* MySQL config delivered by the Main Backend API (identity + persona prompt)
* ``behavior.txt`` loaded from the local agent-core file system (behavior rules)
* safety rules (carried on the backend config)

It holds data only — no I/O, no LLM calls, no LangGraph.
"""

from typing import Any, Dict


class AgentProfile:
    def __init__(
        self,
        agent_id: str,
        display_name: str,
        persona_prompt: str,
        behavior_rules: str,
        safety_rules: Dict[str, Any],
        raw_config: Dict[str, Any],
    ):
        self.agent_id = agent_id
        self.display_name = display_name
        self.persona_prompt = persona_prompt
        self.behavior_rules = behavior_rules
        self.safety_rules = safety_rules
        self.raw_config = raw_config

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the profile for logging / debugging endpoints."""
        return {
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "persona_prompt": self.persona_prompt,
            "behavior_rules": self.behavior_rules,
            "safety_rules": self.safety_rules,
            "raw_config": self.raw_config,
        }

    def __repr__(self) -> str:
        return f"<AgentProfile agent_id={self.agent_id!r} display_name={self.display_name!r}>"
