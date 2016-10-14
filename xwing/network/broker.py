import logging
log = logging.getLogger(__name__)

from xwing.network.connection import Connection
from xwing.network.handshake import connect_handshake, accept_handshake


class Broker:

    def __init__(self, loop, task_pool):
        self.loop = loop
        self.task_pool = task_pool
        self.connection_pool = Pool()

    def get(self, identity):
        return self.connection_pool.get(identity)

    async def connect(self, stream, local_identity, remote_identity):
        connection = Connection(self.loop, stream, self.task_pool)
        await connect_handshake(connection, local_identity)
        self.add(connection, remote_identity)
        return connection

    async def accept_connection(self, stream, local_identity):
        connection = Connection(self.loop, stream, self.task_pool)
        remote_identity = await accept_handshake(connection, local_identity)
        self.add(connection, remote_identity)
        return connection

    def add(self, connection, identity):
        log.debug('Adding new connection to {0}'.format(identity))
        connection.start()
        self.connection_pool.add(identity, connection)

    def __getitem__(self, item):
        return self.connection_pool.__getitem__(item)

    def __contains__(self, item):
        return self.connection_pool.__contains__(item)


class Pool:

    def __init__(self):
        self._connections = {}

    def get(self, identity):
        return self[identity]

    def add(self, identity, connection):
        assert not self._connections.get(identity)
        self._connections[identity] = connection

    def __getitem__(self, item):
        if not isinstance(item, str):
            raise TypeError('Item must be of str type')

        return self._connections[item]

    def __contains__(self, item):
        try:
            self.__getitem__(item)
        except KeyError:
            return False
        return True
