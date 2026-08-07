"""HTTP client for the agent-core /chat API.

Thin forwarding layer used by the chat gateway endpoint for manual/Postman
integration testing. Uses the standard library (consistent with the rest of
this app) so no extra dependency is required.
"""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.conf import settings

from .exceptions import AgentPlatformUnavailable, InvalidAgentPlatformResponse

logger = logging.getLogger(__name__)


def _build_chat_url():
    return urljoin(settings.AGENT_CORE_URL.rstrip('/') + '/', 'chat/')


def send_to_agent_core(payload: dict) -> dict:
    """POST ``payload`` to agent-core's /chat/ endpoint and return its JSON.

    Raises:
        AgentPlatformUnavailable: agent-core is unreachable, timed out, or
            returned an HTTP error.
        InvalidAgentPlatformResponse: agent-core returned a non-JSON body.
    """
    url = _build_chat_url()
    body = json.dumps(payload).encode('utf-8')
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Service-Key': settings.AGENT_CORE_SERVICE_KEY,
    }

    request = Request(url, data=body, headers=headers, method='POST')
    try:
        with urlopen(request, timeout=settings.AGENT_CORE_TIMEOUT_SECONDS) as response:
            raw = response.read().decode('utf-8')
    except HTTPError as exc:
        logger.warning('agent-core returned HTTP error %s.', exc.code)
        raise AgentPlatformUnavailable('agent-core is unavailable.') from exc
    except URLError as exc:
        logger.warning('agent-core connection failed: %s', exc.reason)
        raise AgentPlatformUnavailable('agent-core is unavailable.') from exc
    except TimeoutError as exc:
        logger.warning('agent-core request timed out.')
        raise AgentPlatformUnavailable('agent-core is unavailable.') from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning('agent-core returned invalid JSON.')
        raise InvalidAgentPlatformResponse('agent-core returned invalid JSON.') from exc
