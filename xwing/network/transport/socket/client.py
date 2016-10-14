import logging

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

    def __init__(self, loop, remote_hub_frontend, identity):
        self.loop = loop
        self.remote_hub_frontend = remote_hub_frontend
        self.identity = identity

    async def connect(self, remote_identity):
        address, port = self.remote_hub_frontend.split(':')
        return Connection(self.loop, await connect(
                          self.loop, (address, int(port)), remote_identity))
