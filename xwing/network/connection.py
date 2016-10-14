import asyncio
import time
import logging
log = logging.getLogger(__name__)

from xwing.exceptions import HeartbeatFailureError, ConnectionAlreadyExists

EOL = b'\n'
HEARTBEAT = b'HEARTBEAT'
HEARTBEAT_SIGNAL = b'HEARTBEAT_SIGNAL'
HEARTBEAT_ACK = b'HEARTBEAT_ACK'

INITIAL_HEARBEAT_LIVENESS = 3


class Repository:

    def __init__(self):
        self.connections = {}

    def get(self, identity):
        return self[identity]

    def add(self, connection, identity):
        log.debug('Adding new connection to {0}'.format(identity))
        if self.connections.get(identity):
            raise ConnectionAlreadyExists

        self.connections[identity] = connection

    def __getitem__(self, item):
        if not isinstance(item, str):
            raise TypeError('Item must be of str type')

        return self.connections[item]

    def __contains__(self, item):
        try:
            self.__getitem__(item)
        except KeyError:
            return False

        return True


class Connection:

    def __init__(self, loop, stream, task_pool):
        self.loop = loop
        self.stream = stream
        self.task_pool = task_pool
        self.liveness = INITIAL_HEARBEAT_LIVENESS
        self.stop_event = asyncio.Event()

    def start(self):
        self.task_pool.create_task(self.run_heartbeat_loop())

    async def run_heartbeat_loop(self, heartbeat_interval=5):
        self.start_time = time.time()

        while not self.stop_event.is_set():
            if self.liveness <= 0:
                # TODO now we need to decide how this is going
                # to work. Following this exception, we need to kill
                # this close this connection, delete the mailbox
                # and kill the process
                raise HeartbeatFailureError()

            if time.time() - self.start_time > heartbeat_interval:
                self.liveness -= 1
                self.start_time = time.time()
                self.send(HEARTBEAT_SIGNAL)
                log.debug('Sent hearbeat signal message.')

            await asyncio.sleep(0.1)

    def send(self, data):
        self.stream.write(data + EOL)
        # TODO think more about this, not sure if should be the default case.
        # self.stream.writer.drain()
        return data

    async def recv(self):
        data = await self.stream.readline()

        # TODO may be we can reduce this to one set, just time?
        self.liveness = INITIAL_HEARBEAT_LIVENESS
        self.start_time = time.time()

        while True:
            if not data.startswith(HEARTBEAT):
                break

            if data.startswith(HEARTBEAT_SIGNAL):
                log.debug('Sending heartbeat ack message.')
                self.send(HEARTBEAT_ACK)

            data = await self.stream.readline()

        if data and not data.endswith(EOL):
            log.warning('Received a partial message. '
                        'This may indicate a broken pipe.')
            # TODO may be we need to raise an exception here
            # and only return None when connection is really closed?
            return None

        return data[:-1]


connection_map = {
    'real': Connection,
}


def get_connection(kind):
    return connection_map[kind]
