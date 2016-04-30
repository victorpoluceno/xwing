import logging

import zmq

from xwing.socket.backend.zmq import ZMQBackend

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
        self.backend = ZMQBackend(identity)

    @property
    def identity(self):
        return self.backend.identity

    def recv(self, timeout=None):
        '''Try to recv data. If not data is recv NoData exception will
        raise.

        :param timeout: Timeout in seconds. `None` meaning forever.
        '''
        frames = self.backend.recv_multipart(timeout)
        if not frames:
            return None

        self._frames = frames
        return self._frames[-1]

    def recv_str(self, timeout=None, encoding='utf-8'):
        data = self.recv(timeout)
        if encoding:
            data = data.decode(encoding)

        return data

    def send(self, data):
        '''Send data to connected client.

        :param data: Data to send.
        '''
        # FIXME this state frames mechanics is no good
        # we need a better aproaching. May be go event closer
        # to socket API by implemeting an accept method
        assert self._frames, "Send should always be called after a recv"
        self._frames[-1] = data
        self.backend.send_multipart(self._frames)
        self._frames = None
        return True

    def send_str(self, data, encoding='utf-8'):
        if encoding:
            data = bytes(data, encoding)

        return self.send(data)

    def close(self):
        self.backend.close()

    def bind(self):
        self.backend.connect(zmq.DEALER, self.multiplex_endpoint)

        log.info("Sending ready signal to proxy")
        self.backend.send(self.SIGNAL_READY)
