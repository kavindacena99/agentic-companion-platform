"""Dynamic agent loader (personality engine).

Builds a unified :class:`AgentProfile` by merging:

1. Agent config fetched from the Main Backend API (``GET /api/agents/{id}/``)
2. ``behavior.txt`` loaded from ``agents/{agent_id}/behavior.txt``
3. Safety rules carried on the backend config

Design constraints for this step:

* No hard-coded agents — everything is config-driven.
* No LangGraph and no LLM calls here; this is purely the loader layer.
* The Main Backend is consumed over HTTP only (read-only); its code is never
  imported or modified.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from services.models.agent_profile import AgentProfile

logger = logging.getLogger("agent_core")

# agent-core/agents/  (sibling of the services/ package)
DEFAULT_AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"


class AgentLoaderError(Exception):
    """Base error for the agent loader."""


class AgentConfigError(AgentLoaderError):
    """Raised when the agent config cannot be fetched or is invalid."""


class AgentDisabledError(AgentLoaderError):
    """Raised when an agent exists but is disabled in the Main Backend."""


class AgentLoaderService:
    """Loads agents dynamically. Stateless and safe to instantiate per request."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        service_key: Optional[str] = None,
        timeout: Optional[float] = None,
        agents_dir: Optional[Path] = None,
    ):
        self.base_url = (base_url or os.getenv("MAIN_BACKEND_BASE_URL", "")).rstrip("/")
        self.service_key = service_key or os.getenv("MAIN_BACKEND_SERVICE_KEY", "")
        self.timeout = timeout if timeout is not None else float(
            os.getenv("MAIN_BACKEND_TIMEOUT", "10")
        )
        self.agents_dir = Path(agents_dir) if agents_dir else DEFAULT_AGENTS_DIR

    # ------------------------------------------------------------------
    # FUNCTION 1 — fetch agent config from the Main Backend
    # ------------------------------------------------------------------
    def fetch_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Call ``GET /api/agents/{agent_id}/`` and return the JSON config."""
        if not self.base_url:
            raise AgentConfigError(
                "MAIN_BACKEND_BASE_URL is not configured; cannot fetch agent config."
            )

        url = f"{self.base_url}/api/agents/{agent_id}/"
        headers: Dict[str, str] = {"Accept": "application/json"}
        if self.service_key:
            headers["Authorization"] = f"Bearer {self.service_key}"

        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error("Failed to fetch agent config for %s: %s", agent_id, exc)
            raise AgentConfigError(
                f"Unable to load agent '{agent_id}' from Main Backend."
            ) from exc
        except ValueError as exc:  # invalid JSON
            logger.error("Invalid JSON in agent config for %s: %s", agent_id, exc)
            raise AgentConfigError(
                f"Main Backend returned invalid config for agent '{agent_id}'."
            ) from exc

    # ------------------------------------------------------------------
    # FUNCTION 2 — load behavior.txt from the local file system
    # ------------------------------------------------------------------
    def load_behavior_file(self, agent_id: str) -> str:
        """Return the agent's ``behavior.txt`` contents, or ``""`` if missing.

        A missing or unreadable behavior file must never crash the system.
        """
        path = self.agents_dir / agent_id / "behavior.txt"
        try:
            return path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            logger.warning("No behavior.txt found for agent %s at %s", agent_id, path)
            return ""
        except OSError as exc:
            logger.warning("Could not read behavior.txt for agent %s: %s", agent_id, exc)
            return ""

    # ------------------------------------------------------------------
    # FUNCTION 3 — merge config + behavior + safety into an AgentProfile
    # ------------------------------------------------------------------
    def build_agent_profile(
        self, config: Dict[str, Any], behavior_rules: str
    ) -> AgentProfile:
        agent_id = config.get("agent_id")
        if not agent_id:
            raise AgentConfigError("Agent config is missing 'agent_id'.")

        # Fail closed only on an explicit disable flag; absence means enabled.
        if config.get("enabled", True) is False:
            raise AgentDisabledError(f"Agent '{agent_id}' is disabled.")

        safety_rules = config.get("safety_rules") or {}

        return AgentProfile(
            agent_id=agent_id,
            display_name=config.get("display_name", agent_id),
            persona_prompt=config.get("persona_prompt", ""),
            behavior_rules=behavior_rules,
            safety_rules=safety_rules,
            raw_config=config,
        )

    # ------------------------------------------------------------------
    # FUNCTION 4 — main entry point
    # ------------------------------------------------------------------
    def get_agent(self, agent_id: str) -> AgentProfile:
        """Fetch config, load behavior, and return a unified AgentProfile."""
        config = self.fetch_agent_config(agent_id)
        behavior_rules = self.load_behavior_file(agent_id)
        profile = self.build_agent_profile(config, behavior_rules)
        logger.info("Loaded agent profile: %s", profile)
        return profile
