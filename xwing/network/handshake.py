import asyncio

from xwing.exceptions import HandshakeTimeoutError, HandshakeProtocolError

HANDSHAKE_SIGNAL = b'HANDSHAKE'
HANDSHAKE_ACK_SIGNAL = b'HANDSHAKE_ACK'


async def connect_handshake(connection, local_identity, timeout=10):
    connection.send(b''.join([HANDSHAKE_SIGNAL, b';',
                    local_identity.encode('utf-8')]))
    await connection.stream.drain()

    try:
        handshake_ack = await asyncio.wait_for(connection.recv(), timeout)
    except asyncio.TimeoutError:
        raise HandshakeTimeoutError

    if not handshake_ack.startswith(HANDSHAKE_ACK_SIGNAL):
        raise HandshakeProtocolError

    # TODO implement a identity check and seconde handshake ack.
    return True


async def accept_handshake(connection, local_identity, timeout=10):
    try:
        handshake = await asyncio.wait_for(connection.recv(), timeout)
    except asyncio.TimeoutError:
        raise HandshakeTimeoutError

    if not handshake.startswith(HANDSHAKE_SIGNAL):
        raise HandshakeProtocolError

    remote_identity = handshake.split(b';')[1].strip()
    connection.send(b''.join([HANDSHAKE_ACK_SIGNAL, b';',
                    local_identity.encode('utf-8')]))
    await connection.stream.drain()

    # TODO implement a wait for second hanshake ack here.
    return remote_identity.decode('utf-8')
