class AgentGatewayError(Exception):
    pass


class AgentPlatformUnavailable(AgentGatewayError):
    pass


class InvalidAgentPlatformResponse(AgentGatewayError):
    pass


class AgentRuntimeUnavailable(AgentGatewayError):
    pass


class AgentResponseFailed(AgentGatewayError):
    pass
