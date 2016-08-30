import asyncio
import logging
log = logging.getLogger(__name__)

from xwing.socket.client import Client

DEFAULT_FRONTEND_PORT = 5555
SEPARATOR = b'\n'


class Outbound(object):

    def __init__(self, loop, identity):
        self.loop = loop
        self.identity = identity
        self.clients = {}
        self.connections = {}

    async def connect(self, pid):
        hub_frontend, identity = pid
        if identity not in self.connections:
            if hub_frontend not in self.clients:
                self.clients[hub_frontend] = self.create_client(hub_frontend)

            client = self.clients[hub_frontend]
            self.connections[identity] = await self.create_connection(
                client, identity)

        return self.connections[identity]

    async def create_connection(self, client, identity):
        log.info('Creating connection to %s' % identity)
        while True:
            try:
                conn = await client.connect(identity)
            except ConnectionError:
                log.info('Retrying connection to %s...' % identity)
                await asyncio.sleep(0.1)
                continue
            else:
                break

        return conn

    def create_client(self, hub_frontend):
        log.info('Creating client to %s' % hub_frontend)
        address = hub_frontend
        if ':' not in hub_frontend:
            address = '%s:%d' % (hub_frontend, DEFAULT_FRONTEND_PORT)

        return Client(self.loop, address, self.identity)

    async def send(self, pid, data):
        conn = await self.connect(pid)
        await conn.send(data + SEPARATOR)
