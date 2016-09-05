import asyncio
import logging
import time
log = logging.getLogger(__name__)

from xwing.socket.server import Server
from xwing.mailbox.outbound import SEPARATOR


INITIAL_HEARBEAT_LIVENESS = 3
HEARTBEAT_SIGNAL = b'HEARTBEAT'


async def connection_to_stream(connection, loop):
    return await asyncio.open_connection(sock=connection.sock,
                                         loop=loop)


class HeartbeatFailure(Exception):
    pass


# TODO to avoiding having dead connections forever
# we want to catch hearbeat exceptions and close
# the connection or even expiry connections if don't
# receve data for heartbeat_interval * hertbeat liveness


class Inbound(object):

    def __init__(self, loop, hub_backend, identity):
        self.loop = loop
        self.identity = identity
        self.server = Server(loop, hub_backend, identity)
        self.inbox = asyncio.Queue(loop=self.loop)
        self.stop_event = asyncio.Event()

    async def start(self):
        await self.server.listen()
        self.loop.create_task(self.run_accept_loop())
        log.info('%s is listening.' % self.identity)

    def stop(self):
        self.stop_event.set()

    async def recv(self, timeout=None):
        # TODO, on timeout we may want to return our own
        # custom timeout exception to make API more consistent
        return await asyncio.wait_for(self.inbox.get(), timeout)

    async def run_accept_loop(self, timeout=5.0):
        while not self.stop_event.is_set():
            conn = await self.accept_one(timeout)
            if not conn:
                continue

            # TODO may be we need some kind of limiting here
            self.loop.create_task(self.run_recv_loop(conn, timeout / 5))

    async def accept_one(self, timeout):
        try:
            conn = await asyncio.wait_for(
                self.server.accept(), timeout)
        except asyncio.TimeoutError:
            return None

        return conn

    # TODO the recv data must not be implemented here.
    # Inbound only knowns how accept and create a connection
    async def run_recv_loop(self, conn, timeout, heartbeat_interval=5):
        assert timeout < heartbeat_interval

        liveness = INITIAL_HEARBEAT_LIVENESS
        start_time = time.time()

        reader, writer = await connection_to_stream(conn, self.loop)
        while not self.stop_event.is_set():
            if liveness <= 0:
                raise HeartbeatFailure()

            if time.time() - start_time > heartbeat_interval:
                writer.write(HEARTBEAT_SIGNAL + b'\n')
                start_time = time.time()
                log.debug('Sent hearbeat signal.')

            try:
                data = await self.recv_one(reader, heartbeat_interval)
            except asyncio.TimeoutError:
                liveness -= 1
                continue

            # TODO raise a proper connection error here
            if not data:  # connection is closed
                raise

            liveness = INITIAL_HEARBEAT_LIVENESS
            if data == HEARTBEAT_SIGNAL:
                log.debug('Got heartbeat signal!')
                continue

            await self.inbox.put(data)

    async def recv_one(self, reader, timeout):
        data = await asyncio.wait_for(reader.readline(), timeout)
        if not data:
            return None

        if data and not data.endswith(SEPARATOR):
            log.warning('Received a partial message. '
                        'This may indicate a broken pipe.')
            # TODO may be we need to raise an exception here
            # and only return None when connection s really closed?
            return None

        return data[:-1]
