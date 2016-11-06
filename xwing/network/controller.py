import asyncio

from xwing.network.inbound import Inbound
from xwing.network.outbound import Outbound, Connector
from xwing.network.handshake import connect_handshake, accept_handshake
from xwing.network.connection import Connection, Repository


class Controller:

    def __init__(self, loop, settings, taskset, client_factory,
                 server_factory):
        self.loop = loop
        self.settings = settings
        self.taskset = taskset
        self.repository = Repository()
        self.inbound = Inbound(self.loop, settings)
        self.outbound = Outbound(self.loop, settings)
        self.client_factory = client_factory
        self.server_factory = server_factory
        self.stop_event = asyncio.Event()

    def start(self, timeout=None):
        self.taskset.create_task(self.run_inbound())
        self.taskset.create_task(self.run_outbound(timeout=timeout))

    def stop(self):
        self.stop_event.set()
        self.inbound.stop()

    async def get_inbound(self, *args, **kwargs):
        return await self.inbound.get(*args, **kwargs)

    async def put_outbound(self, *args, **kwargs):
        return await self.outbound.put(*args, **kwargs)

    async def run_outbound(self, timeout=None):
        connector = Connector(self.loop, self.settings,
                              self.client_factory)
        while not self.stop_event.is_set():
            item = await self.outbound.get(timeout=timeout)
            if not item:
                continue

            pid, data = item
            hub_frontend, remote_identity = pid
            if remote_identity not in self.repository:
                stream = await connector.connect(pid)
                connection = Connection(self.loop, stream, self.taskset)
                await connect_handshake(
                    connection, local_identity=self.settings.identity)

                connection.start()
                self.repository.add(connection, remote_identity)
                self.start_receiver(connection)

            connection = self.repository.get(remote_identity)
            connection.send(data)

    async def run_inbound(self):
        stream_server = self.server_factory(self.loop, self.settings)
        await stream_server.listen()
        while not self.stop_event.is_set():
            stream = await stream_server.accept()
            connection = Connection(self.loop, stream, self.taskset)
            remote_identity = await accept_handshake(
                connection, local_identity=self.settings.identity)

            connection.start()
            self.repository.add(connection, remote_identity)
            self.start_receiver(connection)

    def start_receiver(self, connection, timeout=5.0):
        self.taskset.create_task(self.inbound.run_recv_loop(
            connection, timeout / 5))
