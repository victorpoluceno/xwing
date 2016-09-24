class HandshakeError(Exception):
    pass


class HandshakeTimeoutError(HandshakeError):
    pass


class HandshakeProtocolError(HandshakeError):
    pass


class MaxRetriesExceededError(Exception):
    pass


class HeatbeatFailure(Exception):
    pass
