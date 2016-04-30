import uuid

import zmq


ZMQ_LINGER = 0


class ZMQBackend(object):

    def __init__(self, identity):
        self.identity = str(uuid.uuid1()) if not identity else identity
        self.init()

    def init(self):
        self._context = zmq.Context()
        self._poller = zmq.Poller()

    def poll(self, timeout):
        socks = dict(self._poller.poll(timeout))
        if socks.get(self._socket) == zmq.POLLIN:
            return True

        return None

    def close(self):
        # To disconnect we need to unplug current socket
        self._poller.unregister(self._socket)
        self._socket.setsockopt(zmq.LINGER, ZMQ_LINGER)
        self._socket.close()

    def connect(self, kind, multiplex_endpoint):
        self._socket = socket = self._context.socket(kind)
        self._poller.register(socket, zmq.POLLIN)
        socket.setsockopt_string(zmq.IDENTITY, self.identity)
        socket.connect(multiplex_endpoint)

    def recv_multipart(self, timeout=None):
        if not self.poll(timeout):
            return None

        return self._socket.recv_multipart()

    def recv(self, timeout=None):
        if not self.poll(timeout):
            return None

        return self._socket.recv()

    def send_multipart(self, frames):
        self._socket.send_multipart(frames)
        return True

    def send(self, data):
        self._socket.send(data)
        return True
