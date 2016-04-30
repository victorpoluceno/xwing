import logging
import uuid

import zmq


ZMQ_LINGER = 0

SERVICE_POSITIVE_REPLY = b'+'


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

    def __init__(self, multiplex_endpoint, identity=None):
        self.multiplex_endpoint = multiplex_endpoint
        self.identity = str(uuid.uuid1()) if not identity else identity

        self._context = zmq.Context()
        self._poller = zmq.Poller()

    def send(self, data):
        '''
        Send a request to a Server.

        :param data: The payload to send to Server.
        '''
        service = bytes(self.service, 'utf-8')
        self._socket_send(service, data)
        return True

    def send_str(self, data, encoding='utf-8'):
        data = bytes(data, encoding)
        return self.send(data)

    def recv(self, timeout=None):
        '''
        Recv data from Server.

        :param timeout: Timeout in seconds. `None` meaning forever.
        '''
        if not self._run_zmq_poller(timeout):
            return None

        return self._socket.recv()

    def recv_str(self, timeout=None, encoding='utf-8'):
        data = self.recv(timeout)
        if encoding:
            data = data.decode(encoding)

        return data

    def connect(self, service):
        self._socket = self._setup_zmq_socket(
            self._context, self._poller, zmq.REQ, self.identity)
        self._socket.send(bytes(service, 'utf-8'))
        reply = self._socket.recv()
        if reply != SERVICE_POSITIVE_REPLY:
            raise ConnectionRefusedError() # NOQA

        self.service = service
        return True

    def close(self):
        # Socket is confused. Close and remove it.
        self._socket.setsockopt(zmq.LINGER, ZMQ_LINGER)
        self._socket.close()
        self._poller.unregister(self._socket)

    def _socket_send(self, server_identity, payload):
        pack = [payload, server_identity]
        self._socket.send_multipart(pack)

    def _run_zmq_poller(self, timeout):
        socks = dict(self._poller.poll(timeout))
        if socks.get(self._socket) == zmq.POLLIN:
            return True

        return None

    def _setup_zmq_socket(self, context, poller, kind, identity):
        socket = context.socket(kind)
        poller.register(socket, zmq.POLLIN)
        socket.setsockopt_string(zmq.IDENTITY, identity)
        socket.connect(self.multiplex_endpoint)
        return socket
