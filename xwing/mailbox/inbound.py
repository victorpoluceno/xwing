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
        self.loop.create_task(self.accept_loop())
        log.info('%s is listening.' % self.identity)

    def stop(self):
        self.stop_event.set()

    async def recv(self, timeout=None):
        return await asyncio.wait_for(self.inbox.get(), timeout)

    async def accept_loop(self, timeout=5.0):
        while not self.stop_event.is_set():
            try:
                conn = await asyncio.wait_for(
                    self.server.accept(), timeout)
            except asyncio.TimeoutError:
                continue

            # TODO may be we need some kind of limiting here
            self.loop.create_task(self.recv_loop(conn, timeout / 5))

    async def recv_loop(self, conn, timeout):
        while not self.stop_event.is_set():
            try:
                data = await asyncio.wait_for(
                    conn.recv(), timeout)
                if not data:  # connection is closed
                    break
            except asyncio.TimeoutError:
                continue

            await self.inbox.put(data)
