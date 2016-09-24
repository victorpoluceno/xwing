import asyncio

import logging
log = logging.getLogger(__name__)

from xwing.network.handshake import connect_handshake
from xwing.network.transport.stream.client import StreamClient

DEFAULT_FRONTEND_PORT = 5555


class MaxRetriesExceededError(Exception):
    pass


class Connector:

    def __init__(self, loop, identity):
        self.loop = loop
        self.identity = identity
        self.clients = {}

    async def connect(self, pid, max_retries=30, retry_sleep=0.1):
        hub_frontend, identity = pid
        if hub_frontend not in self.clients:
            self.clients[hub_frontend] = self.create_client(hub_frontend)

        client = self.clients[hub_frontend]
        return await self.connect_client(client, identity, max_retries,
                                         retry_sleep)

    async def connect_client(self, client, identity, max_retries, retry_sleep):
        log.info('Creating connection to %s' % identity)
        connection = None
        number_of_retries = 0
        while number_of_retries < max_retries:
            try:
                connection = await client.connect(identity)
            except ConnectionError:
                log.info('Retrying connection to %s...' % identity)
                number_of_retries += 1
                await asyncio.sleep(retry_sleep)
                continue
            else:
                break

        if not connection:
            raise MaxRetriesExceededError

        await connect_handshake(self.identity, connection)
        return connection

    def create_client(self, hub_frontend):
        log.info('Creating client to %s' % hub_frontend)
        address = hub_frontend
        if ':' not in hub_frontend:
            address = '%s:%d' % (hub_frontend, DEFAULT_FRONTEND_PORT)

        return StreamClient(self.loop, address, self.identity)
