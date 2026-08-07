"""Small helpers for reading typed values from environment variables.

Keeps `settings.py` clean and ensures no configuration is hardcoded — every
value comes from the process environment (populated from `.env` via
python-dotenv).
"""

import os
from typing import List, Optional

_TRUE_VALUES = {"1", "true", "yes", "on", "y", "t"}


def env_str(key: str, default: Optional[str] = None) -> Optional[str]:
    """Return the raw string value for ``key`` or ``default`` if unset/empty."""
    value = os.environ.get(key)
    if value is None or value == "":
        return default
    return value


def env_required(key: str) -> str:
    """Return the value for *key* or raise if unset/empty - fail-fast for secrets."""
    value = os.environ.get(key)
    if value is None or value == "":
        raise RuntimeError(f"{key} must be set in the environment.")
    return value


def env_bool(key: str, default: bool = False) -> bool:
    """Return a boolean parsed from common truthy strings."""
    value = os.environ.get(key)
    if value is None or value == "":
        return default
    return value.strip().lower() in _TRUE_VALUES


def env_list(key: str, default: Optional[List[str]] = None, sep: str = ",") -> List[str]:
    """Return a list parsed from a separator-delimited environment variable."""
    value = os.environ.get(key)
    if value is None or value == "":
        return list(default) if default is not None else []
    return [item.strip() for item in value.split(sep) if item.strip()]
