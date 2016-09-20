import asyncio
import logging
log = logging.getLogger(__name__)

from xwing.socket.client import Client

DEFAULT_FRONTEND_PORT = 5555
SEPARATOR = b'\n'  # FIXME should be endof line, not separator
HANDSHAKE_SIGNAL = b'HANDSHAKE'
HANDSHAKE_ACK_SIGNAL = b'ACK_HANDSHAKE'


class MaxRetriesExceededError(Exception):
    pass


class HandshakeError(Exception):
    pass


class HandshakeTimeoutError(HandshakeError):
    pass


class HandshakeProtocolError(HandshakeError):
    pass


class Outbound(object):

    def __init__(self, loop, identity, pool, inbound):
        self.loop = loop
        self.identity = identity
        self.clients = {}
        self.pool = pool
        self.inbound = inbound
        self.outbox = asyncio.Queue(loop=self.loop)
        self.stop_event = asyncio.Event()

    def start(self):
        self.loop.create_task(self.run_send_loop())

    def stop(self):
        self.stop_event.set()

    async def send(self, pid, data):
        await self.outbox.put((pid, data))
        return data

    async def run_send_loop(self, timeout=0.1):
        while not self.stop_event.is_set():
            try:
                pid, data = await asyncio.wait_for(self.outbox.get(),
                                                   timeout=timeout)
            except (asyncio.TimeoutError):
                continue

            try:
                conn = await self.connect(pid)
            except (MaxRetriesExceededError, HandshakeError):
                continue

            await conn.send(data + SEPARATOR)

    async def connect(self, pid, max_retries=30, retry_sleep=0.1):
        hub_frontend, identity = pid
        if identity not in self.pool:
            if hub_frontend not in self.clients:
                self.clients[hub_frontend] = self.create_client(hub_frontend)

            client = self.clients[hub_frontend]
            self.pool.add(identity, await self.connect_client(
                client, identity, max_retries, retry_sleep))
            await self.inbound.start_receiving(self.pool.get(identity))

        return self.pool.get(identity)

    async def connect_client(self, client, identity, max_retries, retry_sleep):
        log.info('Creating connection to %s' % identity)
        conn = None
        number_of_retries = 0
        while number_of_retries < max_retries:
            try:
                conn = await client.connect(identity)
            except ConnectionError:
                log.info('Retrying connection to %s...' % identity)
                number_of_retries += 1
                await asyncio.sleep(retry_sleep)
                continue
            else:
                break

        if not conn:
            raise MaxRetriesExceededError

        await self.handshake(conn)
        return conn

    def create_client(self, hub_frontend):
        log.info('Creating client to %s' % hub_frontend)
        address = hub_frontend
        if ':' not in hub_frontend:
            address = '%s:%d' % (hub_frontend, DEFAULT_FRONTEND_PORT)

        return Client(self.loop, address, self.identity)

    async def handshake(self, conn):
        await conn.send(b''.join([HANDSHAKE_SIGNAL, b';',
                        self.identity.encode('utf-8'),
                        SEPARATOR]))
        try:
            handshake_ack = await asyncio.wait_for(conn.recv(), 10)
        except asyncio.TimeoutError:
            raise HandshakeTimeoutError

        if not handshake_ack != HANDSHAKE_ACK_SIGNAL:
            raise HandshakeProtocolError

        # TODO implement a identity check and seconde handshake ack.
        return True
