import logging
import asyncio

from xwing.network.transport.socket import Connection
from xwing.network.transport.socket.backend.rfc1078 import accept, listen

log = logging.getLogger(__name__)


class Server(object):
    '''The Socket Server implementation.

    Provides an socket that knows how to connect to a proxy
    and receive data from clients.

    :param multiplex_endpoint: Multiplex proxy address to connect.
    :type multiplex_endpoint: str
    :param identity: Unique server identification. If not set uuid1 will be
    used.
    :type identity: str

    Usage::

      >>> from xwing.socket.server import Server
      >>> socket_server = Server('/var/run/xwing.socket', 'server0')
      >>> socket_server.listen()
      >>> conn = socket_server.accept()
      >>> data = conn.recv()
      >>> conn.send(data)
    '''

    def __init__(self, loop, settings):
        self.loop = loop
        self.settings = settings
        self.reconnecting = False

    async def listen(self):
        self.sock = await listen(self.loop, self.settings.hub_backend,
                                 self.settings.identity)
        log.info('%s is listening.' % self.settings.identity)
        return True

    async def reconnect(self):
        self.reconnecting = True
        while True:
            try:
                await self.listen()
            except ConnectionRefusedError:
                await asyncio.sleep(0.1)
            else:
                log.debug('Connection to Hub estabilished.')
                self.reconnecting = False
                break

    async def accept(self):
        if self.reconnecting:
            return None

        conn = await accept(self.loop, self.sock)
        if conn is None:
            log.debug(
                'Connection to Hub lost, starting reconnecting task.')
            self.loop.create_task(self.reconnect())
            return None

        return Connection(self.loop, conn)

    def close(self):
        self.sock.close()
