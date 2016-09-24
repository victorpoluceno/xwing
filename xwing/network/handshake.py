import asyncio


from xwing.network import SEPARATOR

HANDSHAKE_SIGNAL = b'HANDSHAKE'
HANDSHAKE_ACK_SIGNAL = b'ACK_HANDSHAKE'


class HandshakeError(Exception):
    pass


class HandshakeTimeoutError(HandshakeError):
    pass


class HandshakeProtocolError(HandshakeError):
    pass


async def accept_handshake(connection, identity):
    try:
        handshake = await asyncio.wait_for(connection.readline(), 10)
    except asyncio.TimeoutError:
        raise HandshakeTimeoutError

    if not handshake.startswith(HANDSHAKE_SIGNAL):
        raise HandshakeProtocolError

    source_identity = handshake.split(b';')[1].strip()
    connection.write(b''.join([HANDSHAKE_ACK_SIGNAL, b';',
                     identity.encode('utf-8'), SEPARATOR]))
    await connection.drain()

    # TODO implement a wait for second hanshake ack here.
    return source_identity.decode('utf-8')


async def connect_handshake(source_identity, connection):
    connection.write(b''.join([HANDSHAKE_SIGNAL, b';',
                     source_identity.encode('utf-8'),
                     SEPARATOR]))
    await connection.drain()

    try:
        handshake_ack = await asyncio.wait_for(connection.readline(), 10)
    except asyncio.TimeoutError:
        raise HandshakeTimeoutError

    if not handshake_ack != HANDSHAKE_ACK_SIGNAL:
        raise HandshakeProtocolError

    # TODO implement a identity check and seconde handshake ack.
    return True
