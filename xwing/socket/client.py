import logging
import uuid

import zmq


ZMQ_LINGER = 0


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
      >>> client.send('server0', 'ping')
      >>> client.recv()
    '''

    def __init__(self, multiplex_endpoint, identity=None):
        self.multiplex_endpoint = multiplex_endpoint
        self.identity = str(uuid.uuid1()) if not identity else identity

        self._context = zmq.Context()
        self._poller = zmq.Poller()
        self.connect()  # FIXME should be explicitly called

    def send(self, server_identity, request):
        '''
        Send a request to a Server.

        :param server_identity: The Identity of the destination server.
        :param request: The payload to send to Server.
        '''
        server_identity = bytes(server_identity, 'utf-8')
        self._socket_send(server_identity, request)
        return True

    def send_str(self, server_identity, request, encoding='utf-8'):
        request = bytes(request, encoding)
        return self.send(server_identity, request)

    def recv(self, timeout=None):
        '''
        Recv a request from Server.

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

    def _socket_send(self, server_identity, payload):
        pack = [payload, server_identity]
        self._socket.send_multipart(pack)

    def _run_zmq_poller(self, timeout):
        socks = dict(self._poller.poll(timeout))
        if socks.get(self._socket) == zmq.POLLIN:
            return True

        return None

    def connect(self):
        self._socket = self._setup_zmq_socket(
            self._context, self._poller, zmq.REQ, self.identity)

    def _setup_zmq_socket(self, context, poller, kind, identity):
        socket = context.socket(kind)
        poller.register(socket, zmq.POLLIN)
        socket.setsockopt_string(zmq.IDENTITY, identity)
        socket.connect(self.multiplex_endpoint)
        return socket

    def close(self):
        # Socket is confused. Close and remove it.
        self._socket.setsockopt(zmq.LINGER, ZMQ_LINGER)
        self._socket.close()
        self._poller.unregister(self._socket)
