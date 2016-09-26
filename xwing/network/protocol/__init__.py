import asyncio
import time
import logging
log = logging.getLogger(__name__)

from xwing.exceptions import (HandshakeTimeoutError, HandshakeProtocolError,
                              HeartbeatFailureError)

EOL = b'\n'

HANDSHAKE_SIGNAL = b'HANDSHAKE'
HANDSHAKE_ACK_SIGNAL = b'HANDSHAKE_ACK'

HEARTBEAT = b'HEARTBEAT'
HEARTBEAT_SIGNAL = b'HEARTBEAT_SIGNAL'
HEARTBEAT_ACK = b'HEARTBEAT_ACK'

INITIAL_HEARBEAT_LIVENESS = 3


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

    def __init__(self, loop):
        self.loop = loop
        self.connection_pool = Pool()
        self.registered_callbacks = []

    def connection_estabilished(self, callback):
        self.registered_callbacks.append(callback)

    def get(self, identity):
        return self.connection_pool.get(identity)

    async def connect(self, stream, local_identity, remote_identity):
        connection = Connection(self.loop, stream)
        await connect_handshake(connection, local_identity)
        self.add(connection, remote_identity)

    async def accept_connection(self, stream, local_identity):
        connection = Connection(self.loop, stream)
        remote_identity = await accept_handshake(connection, local_identity)
        self.add(connection, remote_identity)

    def add(self, connection, identity):
        log.debug('Adding new connection to {0}'.format(identity))
        connection.start()
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

    def __init__(self, loop, stream):
        self.loop = loop
        self.stream = stream
        self.liveness = INITIAL_HEARBEAT_LIVENESS
        self.stop_event = asyncio.Event()

    def start(self):
        self.loop.create_task(self.run_heartbeat_loop())

    async def run_heartbeat_loop(self, heartbeat_interval=5):
        self.start_time = time.time()

        while not self.stop_event.is_set():
            if self.liveness <= 0:
                # TODO now we need to decide how this is going
                # to work. Following this exception, we need to kill
                # this close this connection, delete the mailbox
                # and kill the process
                raise HeartbeatFailureError()

            if time.time() - self.start_time > heartbeat_interval:
                self.liveness -= 1
                self.start_time = time.time()
                self.send(HEARTBEAT_SIGNAL)
                log.debug('Sent hearbeat signal message.')

            await asyncio.sleep(0.1)

    def send(self, data):
        self.stream.writer.write(data + EOL)
        # TODO think more about this, not sure if should be the default case.
        # self.stream.writer.drain()

    async def recv(self):
        data = await self.stream.readline()

        # TODO may be we can reduce this to one set, just time?
        self.liveness = INITIAL_HEARBEAT_LIVENESS
        self.start_time = time.time()

        while True:
            if not data.startswith(HEARTBEAT):
                break

            if data.startswith(HEARTBEAT_SIGNAL):
                log.debug('Sending heartbeat ack message.')
                self.send(HEARTBEAT_ACK)

            data = await self.stream.readline()

        if data and not data.endswith(EOL):
            log.warning('Received a partial message. '
                        'This may indicate a broken pipe.')
            # TODO may be we need to raise an exception here
            # and only return None when connection is really closed?
            return None

        return data[:-1]
