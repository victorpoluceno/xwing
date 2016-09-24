import logging
import uuid

from xwing.network.transport.socket import Connection
from xwing.network.transport.socket.backend.rfc1078 import connect

log = logging.getLogger(__name__)


class Client(object):
    '''The Socket Client implementation.

    Provide a Client that knowns how to connect to a Proxy service
    send and recv data.

    :param multiplex_endpoint: Mutliplex service address to connect.
    :type multiplex_endpoint: str
    :param identity: Unique client identification. If not set uuid1 will be
    used.
    :type identity: str

    Usage::

      >>> from xwing.socket.client import Client
      >>> client = Client('localhost:5555', 'client1')
      >>> conn = client.connect('server0')
      >>> conn.send(b'ping')
      >>> conn.recv()
    '''

    def __init__(self, loop, multiplex_endpoint, identity=None):
        self.loop = loop
        self.multiplex_endpoint = multiplex_endpoint
        self.identity = str(uuid.uuid1()) if not identity else identity

    async def connect(self, service):
        address, port = self.multiplex_endpoint.split(':')
        return Connection(self.loop, await connect(
                          self.loop, (address, int(port)), service))
