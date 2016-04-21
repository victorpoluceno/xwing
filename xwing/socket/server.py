import logging
import uuid

import zmq


ZMQ_LINGER = 0

log = logging.getLogger(__name__)

# FIXME this server has a problem, if proxy restart
# it doesn't know about the server anymore, so this server
# should sent a ready signal again, but seems like a heartbeating.


class SocketServer(object):
    '''The Socket Server implementation.

    Provides an socket that knows how to connect to a proxy
    and receive data from clients.

    :param multiplex_endpoint: Multiplex proxy address to connect.
    :type multiplex_endpoint: str
    :param identity: Unique server identification. If not set uuid1 will be
    used.
    :type identity: str

    Usage::

      >>> from xwing.socket import SocketServer
      >>> socket_server = SocketServer('ipc:///tmp/0', 'server0')
      >>> socket_server.bind()
      >>> data = socket_server.recv()
      >>> socket_server.send(data)
    '''

    SIGNAL_READY = b"\x01"

    def __init__(self, multiplex_endpoint, identity=None):
        self.multiplex_endpoint = multiplex_endpoint
        self.identity = str(uuid.uuid1()) if not identity else identity

        self._init_zmq_context()

    def recv(self, timeout=None, encoding='utf-8'):
        '''Try to recv data. If not data is recv NoData exception will
        raise.

        :param timeout: Timeout in seconds. `None` meaning forever.
        :param encode: Encoding used to decode from bytes to string.
        '''
        if not self._run_zmq_poller(timeout):
            return None

        self._frames = self._socket.recv_multipart()
        if encoding:
            return self._frames[-1].decode(encoding)

        return self._frames[-1]

    def recv_raw(self, timeout=None):
        return self.recv(timeout, encoding=None)

    def send(self, data, encoding='utf-8'):
        '''Send data to connected client.

        :param data: Data to send.
        :param encode: Encoding used to encode from string to bytes.
        '''
        # FIXME this state frames mechanics is no good
        # we need a better aproaching. May be go event closer
        # to socket API by implemeting an accept method
        assert self._frames, "Send should always be callled after a recv"

        if encoding:
            self._frames[-1] = bytes(data, encoding)
        else:
            self._frames[-1] = data

        self._socket.send_multipart(self._frames)
        self._frames = None
        return True

    def send_raw(self, data):
        return self.send(data, encoding=None)

    def close(self):
        # To disconnect we need to unplug current socket
        self._poller.unregister(self._socket)
        self._socket.setsockopt(zmq.LINGER, ZMQ_LINGER)
        self._socket.close()

    def bind(self):
        self._socket = socket = self._context.socket(zmq.DEALER)
        self._poller.register(socket, zmq.POLLIN)
        socket.setsockopt_string(zmq.IDENTITY, self.identity)
        socket.connect(self.multiplex_endpoint)

        log.info("Sending ready signal to proxy")
        self._socket.send(self.SIGNAL_READY)

    def _init_zmq_context(self):
        self._context = zmq.Context()
        self._poller = zmq.Poller()

    def _run_zmq_poller(self, timeout):
        socks = dict(self._poller.poll(timeout))
        if socks.get(self._socket) == zmq.POLLIN:
            return True

        return None
