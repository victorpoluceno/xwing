import asyncio

from xwing.network.broker import Broker
from xwing.network.inbound import Inbound
from xwing.network.outbound import Outbound, Connector
from xwing.exceptions import MaxRetriesExceededError
from xwing.network.transport.stream.server import get_stream_server
from xwing.network.transport.stream.client import get_stream_client


class Controller:

    def __init__(self, loop, settings, task_pool):
        self.loop = loop
        self.task_pool = task_pool
        self.settings = settings
        self.broker = Broker(self.loop, self.task_pool)
        self.inbound = Inbound(self.loop, settings)
        self.outbound = Outbound(self.loop, settings)
        self.stop_event = asyncio.Event()

    def start(self):
        self.task_pool.create_task(self.run_inbound())
        self.task_pool.create_task(self.run_outbound())

    def stop(self):
        self.inbound.stop()

    async def get_inbound(self, *args, **kwargs):
        return await self.inbound.get(*args, **kwargs)

    async def put_outbound(self, *args, **kwargs):
        return await self.outbound.put(*args, **kwargs)

    async def run_outbound(self):
        connector = Connector(self.loop, self.settings,
                              get_stream_client('real'))
        while not self.stop_event.is_set():
            item = await self.outbound.get()
            if not item:
                continue

            pid, data = item
            hub_frontend, remote_identity = pid
            if remote_identity not in self.broker:
                try:
                    stream = await connector.connect(pid)
                except (MaxRetriesExceededError):
                    continue
                else:
                    connection = await self.broker.connect(
                        stream, self.settings.identity,
                        remote_identity)
                    self.start_receiver(connection)

            connection = self.broker.get(remote_identity)
            connection.send(data)

    async def run_inbound(self):
        stream_server = get_stream_server('real')(self.loop, self.settings)
        await stream_server.listen()
        while not self.stop_event.is_set():
            stream = await stream_server.accept()
            if not stream:
                continue

            connection = await self.broker.accept_connection(
                stream, self.settings.identity)
            self.start_receiver(connection)

    def start_receiver(self, connection, timeout=5.0):
        self.task_pool.create_task(self.inbound.run_recv_loop(
            connection, timeout / 5))
