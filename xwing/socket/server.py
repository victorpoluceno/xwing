import logging
import uuid

from xwing.socket import Connection
from xwing.socket.backend.rfc1078 import accept, listen

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

    def __init__(self, loop, multiplex_endpoint, identity=None):
        self.loop = loop
        self.multiplex_endpoint = multiplex_endpoint
        self.identity = str(uuid.uuid1()) if not identity else identity

    async def listen(self):
        self.sock = await listen(self.loop, self.multiplex_endpoint,
                                 self.identity)

    async def accept(self):
        return Connection(self.loop, await accept(self.loop, self.sock))

    def close(self):
        self.sock.close()
