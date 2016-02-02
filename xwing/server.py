import uuid
import time
from queue import Queue, Empty
import logging
log = logging.getLogger(__name__)

import zmq.green as zmq
import gevent


SIGNAL_READY = b"\x01"
ZMQ_LINGER = 0


class NoData(Exception):
    pass


class Server(object):
    '''The Server implementation.

    Provides an Server that knows how to connect to the Proxy service
    and to process requests from clients. The Server periodicaly checks
    for heartbeats from proxy and reconnects to the Proxy if to many
    heartbeats are missing.

    :param multiplex: Multiplex server address to connect.
    :type multiplex: str
    :param identity: Unique server identification. If not set uuid1 will be used.
    :type identity: str
    :param heartbeat_interval: Interval which heartbeat will be checked in seconds.
    :param heartbeat_liveness: Number of hearbeats that may be missed before
    reconnecting.
    :param reconnect_interval: number of seconds to wait before reconnecting.
    :param reconnect_max_interval: max number of seconds to wait before
    reconnecting.

    Usage::

      >>> from xwing.server import Server
      >>> server = Server('ipc:///tmp/0')
      >>> server.run()
      >>> server.join()
    '''

    def __init__(self, multiplex, identity=None, heartbeat_interval=1,
                 heartbeat_liveness=3, reconnect_interval=1,
                 reconnect_max_interval=32):
        self.multiplex = multiplex
        self.identity = str(uuid.uuid1()) if not identity else identity
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_liveness = heartbeat_liveness
        self.reconnect_interval = reconnect_interval
        self.reconnect_max_interval = reconnect_max_interval

        # For now the receive queue is an infinite queue
        self._receive_queue = Queue(0)
        self._init_zmq_context()

    def run(self):
        '''Run the server loop.'''
        self._greenlet_loop = gevent.spawn(self._run_zmq_poller)
        gevent.sleep(0)

    def join(self):
        ''''Join the server loop blocking until it ends.'''
        self._greenlet_loop.join()

    def recv(self, encoding='utf-8'):
        '''Try to recv data. This will never block instead a NoData
        exception will be raised if no data are available.

        :param encoding: Encoding used to decode from bytes to string.
        '''
        try:
            data = self._receive_queue.get_nowait()
        except Empty:
            raise NoData

        # from bytes to string
        return data.decode(encoding)

    def _init_zmq_context(self):
        self._context = zmq.Context()
        self._poller = zmq.Poller()

    def _setup_zmq_socket(self):
        self._socket = socket = self._context.socket(zmq.DEALER)
        self._poller.register(socket, zmq.POLLIN)
        socket.setsockopt_string(zmq.IDENTITY, self.identity)
        socket.connect(self.multiplex)

        log.info("(%s) server ready" % self.identity)
        socket.send(SIGNAL_READY)

    def _disconnect_zmq_socket(self):
        # To disconnect we need to unplug current socket
        self._poller.unregister(self._socket)
        self._socket.setsockopt(zmq.LINGER, ZMQ_LINGER)
        self._socket.close()

    def _run_zmq_poller(self):
        self._setup_zmq_socket()

        liveness = self.heartbeat_liveness
        interval = self.reconnect_interval

        while True:
            socks = dict(self._poller.poll(self.heartbeat_interval * 1000))
            if socks.get(self._socket) == zmq.POLLIN:
                frames = self._socket.recv_multipart()
                if len(frames) == 1:
                    log.debug("Got proxy heartbeat")
                else:
                    self._receive_queue.put(frames[-1])
                    self._socket.send_multipart(frames)

                # Every time we se some livenees we also want to reset interval
                # so we start from default interval on next reconnection
                liveness = self.heartbeat_liveness
                interval = self.reconnect_interval
                continue

            liveness -= 1
            if liveness == 0:
                log.info("Heartbeat failure, can't reach proxy")
                log.info("Reconnecting in %0.2fs..." % interval)
                time.sleep(interval)

                # We increase reconnection interval up to interval max
                # after that we always reconnect with same value
                if interval < self.reconnect_max_interval:
                    interval *= 2

                self._disconnect_zmq_socket()
                self._setup_zmq_socket()
                liveness = self.heartbeat_liveness
