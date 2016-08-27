import asyncio
import logging
log = logging.getLogger(__name__)

from xwing.socket.server import Server


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

    async def run_recv_loop(self, conn, timeout):
        while not self.stop_event.is_set():
            data = await self.recv_one(conn, timeout)
            if not data:  # connection is closed
                break

            await self.inbox.put(data)

    async def recv_one(self, conn, timeout):
        # TODO need to implement a recv all data until a terminator string
        # is received, this way we avoid breaking pickle serialization.
        # Need to research what teminator to use, '\n'?
        try:
            data = await asyncio.wait_for(conn.recv(), timeout)
        except asyncio.TimeoutError:
            return None

        return data
