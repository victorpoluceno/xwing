import time

import zmq.green as zmq
import gevent

from xwing.client import Client


SIGNAL_READY = b"\x01"  # Signals server is ready
SIGNAL_HEARTBEAT = b"\x02"  # Signals server heartbeat

HEARTBEAT_INTERVAL = 1.0

REQUEST_SIZE = 4
ROUTE_REQUEST_SIZE = 5

REPLY_SIZE = 5
CONTROL_REPLY_SIZE = 2


class Proxy:
    '''The Proxy implementation.

    Provides a Proxy that known how to route messages
    between clients and servers. The proxy also acts as
    proxy to proxy router when a connect client send a request
    to another proxy.

    :param frontend_endpoint: Endpoint where clients will connect.
    :type frontend_endpoint: str
    :param backend_endpoint: Endpoint where servers will connect.
    :type frontend_endpoint: str
    :param heartbeat_interval: Interval used to send heartbeasts in seconds.

    Usage::

      >>> from xwing import Proxy
      >>> proxy = Proxy('tcp://*:5555', 'ipc:///tmp/0')
      >>> proxy.run()
      >>> proxy.join()
    '''

    def __init__(self, frontend_endpoint, backend_endpoint,
                 heartbeat_interval=HEARTBEAT_INTERVAL):
        self.frontend_endpoint = frontend_endpoint
        self.backend_endpoint = backend_endpoint
        self.heartbeat_interval = heartbeat_interval

        self._servers = []
        self._init_zmq_context()

    def run(self):
        '''Run the server loop'''
        self._greenlet_loop = gevent.spawn(self._run_zmq_poller)
        gevent.sleep(0)  # forces the greenlet to be scheduled

    def join(self):
        '''Join the server loop, this will block until loop ends'''
        self._greenlet_loop.join()

    def _init_zmq_context(self):
        self._context = zmq.Context()
        self._poller_backend = zmq.Poller()
        self._poller_proxy = zmq.Poller()

    def _run_zmq_poller(self):
        frontend = self._context.socket(zmq.ROUTER)
        frontend.bind(self.frontend_endpoint)

        backend = self._context.socket(zmq.ROUTER)
        backend.bind(self.backend_endpoint)

        self._poller_backend.register(backend, zmq.POLLIN)
        self._poller_proxy.register(frontend, zmq.POLLIN)
        self._poller_proxy.register(backend, zmq.POLLIN)

        heartbeat_at = time.time() + self.heartbeat_interval

        while True:
            # We only start polling on both sockets if at least
            # one server has already benn seen
            if self._servers:
                poller = self._poller_proxy
            else:
                poller = self._poller_backend

            socks = dict(poller.poll(self.heartbeat_interval * 1000))
            if socks.get(frontend) == zmq.POLLIN:
                frames = frontend.recv_multipart()
                frames_size = len(frames)

                if frames_size == REQUEST_SIZE:
                    self._handle_client_request(backend, frames)
                elif frames_size == ROUTE_REQUEST_SIZE:
                    self._handle_client_route_request(frontend, frames)
                else:
                    raise AssertionError(
                        'Unkown request message: %r' % frames)

            if socks.get(backend) == zmq.POLLIN:
                frames = backend.recv_multipart()
                frames_size = len(frames)

                if frames_size == REPLY_SIZE:
                    self._handle_server_reply(frontend, frames)
                elif frames_size == CONTROL_REPLY_SIZE:
                    self._handle_server_control(frames)
                else:
                    raise AssertionError(
                        'Unkown reply message: %r' % frames)

            # Send heartbeats to idle servers if it's time
            if time.time() >= heartbeat_at:
                for server in self._servers:
                    backend.send_multipart([server, SIGNAL_HEARTBEAT])

                heartbeat_at = time.time() + self.heartbeat_interval

    def _handle_server_reply(self, frontend, reply):
        # Handle a reply from a server to a client.
        # Message format: [server_identity, '', client_identity, '', payload]
        client_identity, _, payload = reply[2:]
        frontend.send_multipart([client_identity, _, payload])

    def _handle_server_control(self, control):
        # Handle control messages from server to proxy.
        # Message format: [server_identity, payload]
        server_identity, payload = control
        assert payload == SIGNAL_READY
        if server_identity not in self._servers:
            self._servers.append(server_identity)

    def _handle_client_request(self, backend, request):
        client_identity, _, payload, server_identity = request
        backend.send_multipart(
            [server_identity, b'', client_identity, b'', payload])

    def _handle_client_route_request(self, frontend, request):
        # A route request is a request that must be routed to another
        # proxy. The destination multiplex it's the last part
        # of the message.
        client_identity, _, payload, server_identity, multiplex = request
        reply = Client(multiplex).send(server_identity, payload)
        if not reply:
            return

        # If got a reply just send it back to the original client
        frontend.send_multipart([client_identity, b'', reply])
