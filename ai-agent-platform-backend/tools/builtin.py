"""Built-in tools shipped with agent-core.

Four typed tools cover the initial "let the agent act" surface:

* :class:`SetReminderTool`      — schedule a reminder for the user.
* :class:`SuggestActivityTool`  — recommend an activity (optionally mood-aware).
* :class:`FetchUserProfileTool` — read the user's profile from the Main Backend.
* :class:`SearchWebTool`        — web search (guarded: off unless configured).

Each tool is deterministic where it can be and degrades to a clean error
observation otherwise — tools never raise (see :meth:`Tool.execute`).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Callable, Dict, Optional

from tools.base import Tool, ToolResult

logger = logging.getLogger("agent_core")


# ----------------------------------------------------------------------
# set_reminder
# ----------------------------------------------------------------------
class SetReminderTool(Tool):
    name = "set_reminder"
    description = (
        "Schedule a reminder for the user at a given time. Use when the user asks "
        "to be reminded about something (e.g. 'remind me at 8pm to call mom')."
    )
    parameters = {
        "type": "object",
        "properties": {
            "time": {
                "type": "string",
                "description": "When to remind, in the user's words (e.g. '8pm', 'tomorrow 9am').",
            },
            "message": {
                "type": "string",
                "description": "What to remind the user about.",
            },
        },
        "required": ["time", "message"],
    }

    # Very small, forgiving time normalizer — enough to echo a clean confirmation.
    _TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", re.IGNORECASE)

    def _normalize_time(self, raw: str) -> str:
        match = self._TIME_RE.search(raw or "")
        if not match:
            return (raw or "").strip()
        hour = int(match.group(1))
        minute = match.group(2) or "00"
        meridiem = match.group(3).lower()
        return f"{hour}:{minute} {meridiem}"

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        missing = self._require(arguments, "time", "message")
        if missing:
            return ToolResult(ok=False, error=f"missing required argument '{missing}'")

        when = self._normalize_time(str(arguments["time"]))
        message = str(arguments["message"]).strip()
        user_id = context.get("user_id", "")
        logger.info("set_reminder for user=%s at %s: %s", user_id, when, message)
        return ToolResult(
            ok=True,
            data={"status": "scheduled", "time": when, "message": message},
        )


# ----------------------------------------------------------------------
# suggest_activity
# ----------------------------------------------------------------------
class SuggestActivityTool(Tool):
    name = "suggest_activity"
    description = (
        "Suggest an activity for the user, optionally tailored to their mood. Use "
        "when the user is bored, unsure what to do, or asks for ideas."
    )
    parameters = {
        "type": "object",
        "properties": {
            "mood": {
                "type": "string",
                "description": "The user's current mood, if known (e.g. 'sad', 'bored', 'anxious').",
            }
        },
        "required": [],
    }

    _BY_MOOD = {
        "sad": "a gentle walk outside and calling someone you trust",
        "lonely": "joining an online community around a hobby you enjoy",
        "anxious": "a 5-minute breathing exercise, then a small tidy-up task",
        "bored": "trying a 15-minute sketch or learning three words of a new language",
        "tired": "a short rest, some water, and a calming playlist",
        "happy": "capturing the moment in a journal or sharing it with a friend",
    }
    _DEFAULT = "a short walk, some music, or jotting down three things on your mind"

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        mood = str(arguments.get("mood") or context.get("emotion") or "").strip().lower()
        suggestion = self._BY_MOOD.get(mood, self._DEFAULT)
        return ToolResult(ok=True, data={"suggestion": suggestion, "mood": mood or "unknown"})


# ----------------------------------------------------------------------
# fetch_user_profile
# ----------------------------------------------------------------------
class FetchUserProfileTool(Tool):
    name = "fetch_user_profile"
    description = (
        "Look up the user's saved profile (name, bio, language, timezone) from the "
        "Main Backend. Use when personalizing a reply depends on profile details."
    )
    parameters = {"type": "object", "properties": {}, "required": []}

    def __init__(
        self,
        base_url: Optional[str] = None,
        service_key: Optional[str] = None,
        timeout: Optional[float] = None,
        http_get: Optional[Callable[..., Any]] = None,
    ):
        self._base_url = base_url
        self._service_key = service_key
        self._timeout = timeout
        self._http_get = http_get  # injectable for tests

    def _get(self, url, headers, params, timeout):
        if self._http_get is not None:
            return self._http_get(url, headers=headers, params=params, timeout=timeout)
        import requests

        return requests.get(url, headers=headers, params=params, timeout=timeout)

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        base_url = (self._base_url or os.getenv("MAIN_BACKEND_BASE_URL", "")).rstrip("/")
        if not base_url:
            return ToolResult(ok=False, error="user profile lookup is not configured")

        user_id = context.get("user_id", "")
        if not user_id:
            return ToolResult(ok=False, error="no user_id in context")

        service_key = self._service_key or os.getenv("MAIN_BACKEND_SERVICE_KEY", "")
        timeout = self._timeout if self._timeout is not None else float(
            os.getenv("MAIN_BACKEND_TIMEOUT", "10")
        )
        headers = {"Accept": "application/json"}
        if service_key:
            headers["Authorization"] = f"Bearer {service_key}"

        response = self._get(
            f"{base_url}/api/profile/",
            headers=headers,
            params={"user_id": user_id},
            timeout=timeout,
        )
        status = getattr(response, "status_code", 500)
        if status != 200:
            return ToolResult(ok=False, error=f"profile lookup failed (HTTP {status})")

        profile = response.json() or {}
        # Only surface non-sensitive, useful fields.
        keep = {k: profile.get(k) for k in ("display_name", "bio", "language", "timezone") if profile.get(k)}
        return ToolResult(ok=True, data=keep or {"profile": "empty"})


# ----------------------------------------------------------------------
# search_web (guarded)
# ----------------------------------------------------------------------
class SearchWebTool(Tool):
    name = "search_web"
    description = (
        "Search the web for current, factual information the agent does not know. "
        "Use only for real-time facts (news, weather, prices)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query."},
        },
        "required": ["query"],
    }

    def __init__(self, search_fn: Optional[Callable[[str], Any]] = None):
        # Injectable backend. Absent + unconfigured env → tool stays guarded off.
        self._search_fn = search_fn

    def run(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        missing = self._require(arguments, "query")
        if missing:
            return ToolResult(ok=False, error="missing required argument 'query'")

        if self._search_fn is None:
            # No provider wired up — guard it so we never fabricate results.
            return ToolResult(ok=False, error="web search is not configured")

        results = self._search_fn(str(arguments["query"]))
        return ToolResult(ok=True, data={"results": results})
