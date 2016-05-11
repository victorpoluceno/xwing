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

    def __init__(self, multiplex_endpoint, identity=None):
        self.multiplex_endpoint = multiplex_endpoint
        self.identity = str(uuid.uuid1()) if not identity else identity

    def listen(self):
        self.sock = listen(self.multiplex_endpoint, self.identity)

    def accept(self):
        return Connection(accept(self.sock))

    def close(self):
        self.sock.close()
