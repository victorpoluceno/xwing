import asyncio
import logging
log = logging.getLogger(__name__)


class Inbound:

    def __init__(self, loop, settings):
        self.loop = loop
        self.settings = settings
        self.inbox = asyncio.Queue(loop=self.loop)
        self.stop_event = asyncio.Event()

    def stop(self):
        self.stop_event.set()

    async def get(self, timeout=None):
        try:
            data = await asyncio.wait_for(self.inbox.get(), timeout)
        except asyncio.TimeoutError:
            return None
        return data

    async def run_recv_loop(self, connection, timeout=None):
        while not self.stop_event.is_set():
            try:
                data = await asyncio.wait_for(connection.recv(), timeout)
            except asyncio.TimeoutError:
                continue

            if not data:  # connection is closed
                break

            await self.inbox.put(data)
