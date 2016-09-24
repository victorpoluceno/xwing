import asyncio
import logging
log = logging.getLogger(__name__)

from xwing.network import SEPARATOR
from xwing.network.handshake import HandshakeError
from xwing.network.protocol.outbound.connector import (
    Connector, MaxRetriesExceededError)


class Outbound(object):

    def __init__(self, loop, identity, connection_pool, inbound):
        self.loop = loop
        self.identity = identity
        self.connection_pool = connection_pool
        self.inbound = inbound
        self.connector = Connector(self.loop, identity)
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

            hub_frontend, identity = pid
            if identity not in self.connection_pool:
                try:
                    connection = await self.connector.connect(pid)
                except (MaxRetriesExceededError, HandshakeError):
                    continue
                else:
                    self.connection_pool.add(identity, connection)
                    await self.inbound.start_receiving(connection)

            connection = self.connection_pool.get(identity)
            connection.write(data + SEPARATOR)
