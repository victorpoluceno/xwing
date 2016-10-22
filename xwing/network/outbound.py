import asyncio
import logging
log = logging.getLogger(__name__)

from xwing.exceptions import MaxRetriesExceededError

DEFAULT_FRONTEND_PORT = 5555


class Connector:

    def __init__(self, loop, settings, client_factory):
        self.loop = loop
        self.settings = settings
        self.client_factory = client_factory
        self.clients = {}

    async def connect(self, pid):
        hub_frontend, identity = pid
        if hub_frontend not in self.clients:
            self.clients[hub_frontend] = self.create_client(hub_frontend)

        client = self.clients[hub_frontend]
        return await self.connect_client(client, identity)

    async def connect_client(self, client, remote_identity, max_retries=30,
                             retry_sleep=0.1):
        log.info('Creating connection to %s' % remote_identity)
        connection = None
        number_of_retries = 0
        while number_of_retries < max_retries:
            try:
                connection = await client.connect(remote_identity)
            except ConnectionError:
                log.info('Retrying connection to %s...' % remote_identity)
                number_of_retries += 1
                await asyncio.sleep(retry_sleep)
                continue
            else:
                break

        if not connection:
            raise MaxRetriesExceededError

        return connection

    def create_client(self, remote_hub_frontend):
        log.info('Creating client to %s' % remote_hub_frontend)
        remote_address = remote_hub_frontend
        if ':' not in remote_hub_frontend:
            remote_address = '%s:%d' % (
                remote_hub_frontend, DEFAULT_FRONTEND_PORT)

        return self.client_factory(
            self.loop, remote_hub_frontend=remote_address,
            identity=self.settings.identity)


class Outbound(object):

    def __init__(self, loop, settings):
        self.loop = loop
        self.outbox = asyncio.Queue(loop=self.loop)

    async def put(self, pid, data):
        await self.outbox.put((pid, data))
        return data

    async def get(self, timeout=None):
        try:
            item = await asyncio.wait_for(self.outbox.get(),
                                          timeout=timeout)
        except asyncio.TimeoutError:
            return None

        return item
