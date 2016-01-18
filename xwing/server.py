import time
import threading

import zmq


PPP_READY = b"\x01"

HEARTBEAT_INTERVAL = 1
HEARTBEAT_LIVENESS = 3

INTERVAL_INIT = 1
INTERVAL_MAX = 32


# TODO implement worker to proxy heartbeat


class Server(threading.Thread):

    def __init__(self, address, identity):
        super(Server, self).__init__()

        self.address = address
        self.identity = identity

        self._context = zmq.Context()
        self._poller = zmq.Poller()

    def on_recv(self, callback):
        self.callback = callback

    def send(self, frames):
        self._socket.send_multipart(frames)

    def run(self):
        self._socket = self._setup()
        self._loop()

    def _loop(self):
        liveness = HEARTBEAT_LIVENESS
        interval = INTERVAL_INIT

        while True:
            socks = dict(self._poller.poll(HEARTBEAT_INTERVAL * 1000))
            if socks.get(self._socket) == zmq.POLLIN:
                frames = self._socket.recv_multipart()
                if len(frames) == 1:
                    print("I: Proxy heartbeat")
                    liveness = HEARTBEAT_LIVENESS
                else:
                    self.callback(self, frames)
                    liveness = HEARTBEAT_LIVENESS

                # Every time we se some livenees we also want
                # too reset interval, so we start from default interval
                # on next reconnection
                interval = INTERVAL_INIT
            else:
                liveness -= 1
                if liveness == 0:
                    print("W: Heartbeat failure, can't reach proxy")
                    print("W: Reconnecting in %0.2fs..." % interval)
                    time.sleep(interval)

                    # We increase reconnection interval up to interval max
                    # after that we always reconnect with same value
                    if interval < INTERVAL_MAX:
                        interval *= 2

                    # To disconnect we need to unplug current socket
                    self._poller.unregister(self._socket)
                    self._socket.setsockopt(zmq.LINGER, 0)
                    self._socket.close()

                    self._socket = self._setup()
                    liveness = HEARTBEAT_LIVENESS

    def _setup(self):
        socket = self._context.socket(zmq.DEALER)
        self._poller.register(socket, zmq.POLLIN)

        socket.setsockopt_string(zmq.IDENTITY, self.identity)
        socket.connect(self.address)

        print("I: (%s) server ready" % self.identity)
        socket.send(PPP_READY)
        return socket
