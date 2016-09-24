import asyncio
import logging
log = logging.getLogger(__name__)

from xwing.exceptions import HandshakeTimeoutError, HandshakeProtocolError

EOL = b'\n'
HANDSHAKE_SIGNAL = b'HANDSHAKE'
HANDSHAKE_ACK_SIGNAL = b'ACK_HANDSHAKE'


async def connect_handshake(connection, local_identity):
    connection.send(b''.join([HANDSHAKE_SIGNAL, b';',
                    local_identity.encode('utf-8')]))
    await connection.stream.drain()

    try:
        handshake_ack = await asyncio.wait_for(connection.recv(), 10)
    except asyncio.TimeoutError:
        raise HandshakeTimeoutError

    if not handshake_ack.startswith(HANDSHAKE_ACK_SIGNAL):
        raise HandshakeProtocolError

    # TODO implement a identity check and seconde handshake ack.
    return True


async def accept_handshake(connection, local_identity):
    try:
        handshake = await asyncio.wait_for(connection.recv(), 10)
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


class Broker:

    def __init__(self):
        self.connection_pool = Pool()
        self.registered_callbacks = []

    def connection_estabilished(self, callback):
        self.registered_callbacks.append(callback)

    def get(self, identity):
        return self.connection_pool.get(identity)

    async def connect(self, stream, local_identity, remote_identity):
        connection = Connection(stream)
        await connect_handshake(connection, local_identity)
        self.add(connection, remote_identity)

    async def accept_connection(self, stream, local_identity):
        connection = Connection(stream)
        remote_identity = await accept_handshake(connection, local_identity)
        self.add(connection, remote_identity)

    def add(self, connection, identity):
        log.debug('Adding new connection to {0}'.format(identity))
        self.connection_pool.add(identity, connection)
        for callback in self.registered_callbacks:
            callback(identity, connection)

    def __getitem__(self, item):
        return self.connection_pool.__getitem__(item)

    def __contains__(self, item):
        return self.connection_pool.__contains__(item)


class Pool:

    def __init__(self):
        self._connections = {}

    def get(self, identity):
        return self[identity]

    def add(self, identity, connection):
        assert not self._connections.get(identity)
        self._connections[identity] = connection

    def __getitem__(self, item):
        if not isinstance(item, str):
            raise TypeError('Item must be of str type')

        return self._connections[item]

    def __contains__(self, item):
        try:
            self.__getitem__(item)
        except KeyError:
            return False
        return True


class Connection:

    def __init__(self, stream):
        self.stream = stream

    def send(self, data):
        self.stream.writer.write(data + EOL)
        # TODO think more about this, not sure if should be
        # the default case.
        # self.stream.writer.drain()

    async def recv(self):
        data = await self.stream.readline()
        if data and not data.endswith(EOL):
            log.warning('Received a partial message. '
                        'This may indicate a broken pipe.')
            # TODO may be we need to raise an exception here
            # and only return None when connection is really closed?
            return None

        return data[:-1]
