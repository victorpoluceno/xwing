import asyncio
import logging
log = logging.getLogger(__name__)

from xwing.network.protocol.inbound.listener import Listener


class Inbound(object):

    def __init__(self, loop, hub_backend, identity, broker):
        self.loop = loop
        self.identity = identity
        self.broker = broker
        self.listener = Listener(loop, hub_backend, identity)
        self.inbox = asyncio.Queue(loop=self.loop)
        self.stop_event = asyncio.Event()

    async def start(self):
        await self.listener.listen()
        self.loop.create_task(self.run_accept_loop())

    def stop(self):
        self.stop_event.set()

    async def recv(self, timeout=None):
        # TODO, on timeout we may want to return our own
        # custom timeout exception to make API more consistent
        return await asyncio.wait_for(self.inbox.get(), timeout)

    async def run_accept_loop(self, timeout=5.0):
        while not self.stop_event.is_set():
            stream = await self.listener.accept(timeout)
            if not stream:
                continue

            await self.broker.accept_connection(stream, self.identity)

    def start_receiving(self, identity, connection, timeout=5.0):
        # TODO may be we need some kind of limiting here
        self.loop.create_task(self.run_recv_loop(connection, timeout / 5))

    async def run_recv_loop(self, connection, timeout):
        while not self.stop_event.is_set():
            try:
                data = await asyncio.wait_for(connection.recv(), timeout)
            except asyncio.TimeoutError:
                continue

            if not data:  # connection is closed
                break

            await self.inbox.put(data)
