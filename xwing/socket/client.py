import logging

import zmq

from xwing.socket.backend.zmq import ZMQBackend


log = logging.getLogger(__name__)


class SocketClient(object):
    '''The Socket Client implementation.

    Provide a Client that knowns how to connect to a Proxy service
    send requests and waiting for replies.

    :param multiplex_endpoint: Mutliplex service address to connect.
    :type multiplex_endpoint: str
    :param identity: Unique client identification. If not set uuid1 will be
    used.
    :type identity: str

    Usage::

      >>> from xwing.socket import SocketClient
      >>> client = SocketClient('tcp://localhost:5555', 'client1')
      >>> client.connect('server0')
      >>> client.send(b'ping')
      >>> client.recv()
    '''

    SERVICE_POSITIVE_REPLY = b'+'

    def __init__(self, multiplex_endpoint, identity=None):
        self.multiplex_endpoint = multiplex_endpoint
        self.backend = ZMQBackend(identity)

    @property
    def identity(self):
        return self.backend.identity

    def send(self, data):
        '''
        Send a request to a Server.

        :param data: The payload to send to Server.
        '''
        service = bytes(self.service, 'utf-8')
        self.backend.send_multipart([data, service])
        return True

    def send_str(self, data, encoding='utf-8'):
        data = bytes(data, encoding)
        return self.send(data)

    def recv(self, timeout=None):
        '''
        Recv data from Server.

        :param timeout: Timeout in seconds. `None` meaning forever.
        '''
        if not self.backend.poll(timeout):
            return None

        return self.backend.recv()

    def recv_str(self, timeout=None, encoding='utf-8'):
        data = self.recv(timeout)
        if encoding:
            data = data.decode(encoding)

        return data

    def connect(self, service):
        self.backend.connect(zmq.REQ, self.multiplex_endpoint)
        self.backend.send(bytes(service, 'utf-8'))
        reply = self.backend.recv()
        if reply != self.SERVICE_POSITIVE_REPLY:
            raise ConnectionRefusedError() # NOQA

        self.service = service
        return True

    def close(self):
        self.backend.close()
