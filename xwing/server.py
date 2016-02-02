import gevent
from gevent import monkey
monkey.patch_all()

import uuid
import time
from queue import Queue, Empty
import logging
logger = logging.getLogger(__name__)

import zmq.green as zmq


PPP_READY = b"\x01"


class NoData(Exception):
    pass


class Server(object):

    def __init__(self, multiplex_address, identity=None, heartbeat_interval=1,
                 heartbeat_liveness=3, reconnect_interval=1,
                 reconnect_max_interval=32):
        '''The Server implementation.

        @multiplex_address full multiplex address where to connect to.
        @identity server unique identification. If not set uuid1 will be used.
        @heartbeat_interval interval which heartbeat is checked in seconds.
        @heartbeat_liveness number of hearbeat may be missed before trying
        to reconnect.
        @reconnect_interval number of seconds to wait before reconnecting.
        @reconnect_max_interval max number of seconds to wait before
        reconnecting.'''
        self.multiplex_address = multiplex_address
        self.identity = str(uuid.uuid1()) if not identity else identity
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_liveness = heartbeat_liveness
        self.reconnect_interval = reconnect_interval
        self.reconnect_max_interval = reconnect_max_interval

        self._receive_queue = Queue(0)
        self._init_zmq_context()

    def run(self):
        '''Run the server loop'''
        self._greenlet_loop = gevent.spawn(self._run_zmq_poller)
        gevent.sleep(0)

    def join(self):
        ''''Join the server loop, this will block until loop ends'''
        self._greenlet_loop.join()

    def recv(self):
        '''Try to recv data. This will never blockin, instead an NoData
        exception will be raised.'''
        try:
            data = self._receive_queue.get_nowait()
        except Empty:
            raise NoData

        # from bytes to string
        return data.decode('utf-8')

    def _init_zmq_context(self):
        self._context = zmq.Context()
        self._poller = zmq.Poller()

    def _setup_zmq_socket(self):
        self._socket = socket = self._context.socket(zmq.DEALER)
        self._poller.register(socket, zmq.POLLIN)
        socket.setsockopt_string(zmq.IDENTITY, self.identity)
        socket.connect(self.multiplex_address)

        logger.info("(%s) server ready" % self.identity)
        socket.send(PPP_READY)

    def _run_zmq_poller(self):
        self._setup_zmq_socket()

        liveness = self.heartbeat_liveness
        interval = self.reconnect_interval

        while True:
            socks = dict(self._poller.poll(self.heartbeat_interval * 1000))
            if socks.get(self._socket) == zmq.POLLIN:
                frames = self._socket.recv_multipart()
                if len(frames) == 1:
                    logger.debug("Got proxy heartbeat")
                    liveness = self.heartbeat_liveness
                else:
                    self._receive_queue.put(frames[-1])
                    self._socket.send_multipart(frames)
                    liveness = self.heartbeat_liveness

                # Every time we se some livenees we also want
                # too reset interval, so we start from default interval
                # on next reconnection
                interval = self.reconnect_interval
                continue

            liveness -= 1
            if liveness == 0:
                logger.info("Heartbeat failure, can't reach proxy")
                logger.info("Reconnecting in %0.2fs..." % interval)
                time.sleep(interval)

                # We increase reconnection interval up to interval max
                # after that we always reconnect with same value
                if interval < self.reconnect_max_interval:
                    interval *= 2

                # To disconnect we need to unplug current socket
                self._poller.unregister(self._socket)
                self._socket.setsockopt(zmq.LINGER, 0)
                self._socket.close()

                self._setup_zmq_socket()
                liveness = self.heartbeat_liveness
