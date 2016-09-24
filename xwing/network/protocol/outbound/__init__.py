import asyncio
import logging
log = logging.getLogger(__name__)


from xwing.exceptions import HandshakeError, MaxRetriesExceededError
from xwing.network.protocol.outbound.connector import Connector


class Outbound(object):

    def __init__(self, loop, identity, broker):
        self.loop = loop
        self.identity = identity
        self.broker = broker
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

            hub_frontend, remote_identity = pid
            if remote_identity not in self.broker:
                try:
                    stream = await self.connector.connect(pid)
                except (MaxRetriesExceededError):
                    continue
                else:
                    await self.broker.connect(stream, self.identity,
                                              remote_identity)

            connection = self.broker.get(remote_identity)
            connection.send(data)
