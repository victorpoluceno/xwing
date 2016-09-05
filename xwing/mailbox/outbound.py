import asyncio
import logging
import time
log = logging.getLogger(__name__)

from xwing.socket.client import Client

INITIAL_HEARBEAT_LIVENESS = 3

DEFAULT_FRONTEND_PORT = 5555
SEPARATOR = b'\n'


class MaxRetriesExceededError(Exception):
    pass


class HeartbeatFailure(Exception):
    pass


# TODO need to implement a way to reconnect on heartbeat failure
# basically we want to catch a heartbeat exception, close current
# client connection and start a new one. We start a new one after
# some time and increment this time everytime we get a heartbeat
# failure up to a max number.

class Outbound(object):

    def __init__(self, loop, identity):
        self.loop = loop
        self.identity = identity
        self.clients = {}
        self.connections = {}
        self.stop_event = asyncio.Event()

    def stop(self):
        self.stop_event.set()

    async def run_heartbeat_loop(self, connection, heartbeat_interval=5):
        liveness = INITIAL_HEARBEAT_LIVENESS
        start_time = time.time()

        while not self.stop_event.is_set():
            if liveness <= 0:
                raise HeartbeatFailure()

            if time.time() - start_time > heartbeat_interval:
                start_time = time.time()
                await connection.send(b'HEARTBEAT\n')
                log.debug('Sent hearbeat signal.')

            try:
                data = await asyncio.wait_for(connection.recv(),
                                              heartbeat_interval)
            except asyncio.TimeoutError:
                liveness -= 1
                continue

            # TODO raise a proper connection error here
            if not data:
                raise

            log.debug('Got heartbeat signal!')
            liveness = INITIAL_HEARBEAT_LIVENESS

    async def send(self, pid, data):
        conn = await self.connect(pid)
        return await conn.send(data + SEPARATOR)

    async def connect(self, pid, max_retries=30, retry_sleep=0.1):
        hub_frontend, identity = pid
        if identity not in self.connections:
            if hub_frontend not in self.clients:
                self.clients[hub_frontend] = self.create_client(hub_frontend)

            client = self.clients[hub_frontend]
            self.connections[identity] = await self.connect_client(
                client, identity, max_retries, retry_sleep)
            self.loop.create_task(self.run_heartbeat_loop(
                self.connections[identity]))

        return self.connections[identity]

    async def connect_client(self, client, identity, max_retries, retry_sleep):
        log.info('Creating connection to %s' % identity)
        conn = None
        number_of_retries = 0
        while number_of_retries < max_retries:
            try:
                conn = await client.connect(identity)
            except ConnectionError:
                log.info('Retrying connection to %s...' % identity)
                number_of_retries += 1
                await asyncio.sleep(retry_sleep)
                continue
            else:
                break

        if not conn:
            raise MaxRetriesExceededError

        return conn

    def create_client(self, hub_frontend):
        log.info('Creating client to %s' % hub_frontend)
        address = hub_frontend
        if ':' not in hub_frontend:
            address = '%s:%d' % (hub_frontend, DEFAULT_FRONTEND_PORT)

        return Client(self.loop, address, self.identity)
