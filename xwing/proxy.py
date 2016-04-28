import logging
import threading

import zmq


SIGNAL_READY = b"\x01"  # Signals server is ready

REPLY_SIZE = 5
CONTROL_REPLY_SIZE = 2
SERVICE_QUERY_SIZE = 3
CLIENT_REQUEST_SIZE = 4

POLLING_INTERVAL = 1.0

ZMQ_LINGER = 0

log = logging.getLogger(__name__)


class Proxy:
    '''The Socket Proxy implementation.

    Provides a Proxy that known how to route messages
    between clients and servers.

    :param frontend_endpoint: Endpoint where clients will connect.
    :type frontend_endpoint: str
    :param backend_endpoint: Endpoint where servers will connect.
    :type frontend_endpoint: str
    :param polling_interval: Interval used on polling socket in seconds.

    Usage::

      >>> from xwing.socket import SocketProxy
      >>> proxy = SocketProxy('tcp://*:5555', 'ipc:///tmp/0')
      >>> proxy.run()
    '''

    def __init__(self, frontend_endpoint, backend_endpoint,
                 polling_interval=POLLING_INTERVAL):
        self.frontend_endpoint = frontend_endpoint
        self.backend_endpoint = backend_endpoint
        self.polling_interval = polling_interval

        self._run_loop = False
        self._servers = []
        self._init_zmq_context()

    def run(self, forever=True):
        '''Run the server loop'''
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run_zmq_poller)
        self.thread.daemon = False
        self.thread.start()
        if forever:
            try:
                self.thread.join()
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        '''Loop stop.'''
        self.stop_event.set()
        self.thread.join()
        self._disconnect_zmq_socket()

    def _disconnect_zmq_socket(self):
        # To disconnect we need to unplug current socket
        self._poller_backend.unregister(self._backend)
        self._poller_proxy.unregister(self._frontend)
        self._poller_proxy.unregister(self._backend)

        self._frontend.setsockopt(zmq.LINGER, ZMQ_LINGER)
        self._backend.setsockopt(zmq.LINGER, ZMQ_LINGER)

        self._frontend.close()
        self._backend.close()

    def _init_zmq_context(self):
        self._context = zmq.Context()
        self._poller_backend = zmq.Poller()
        self._poller_proxy = zmq.Poller()

    def _run_zmq_poller(self):
        self._frontend = frontend = self._context.socket(zmq.ROUTER)
        self._frontend.bind(self.frontend_endpoint)

        self._backend = backend = self._context.socket(zmq.ROUTER)
        self._backend.bind(self.backend_endpoint)

        self._poller_backend.register(self._backend, zmq.POLLIN)
        self._poller_proxy.register(self._frontend, zmq.POLLIN)
        self._poller_proxy.register(self._backend, zmq.POLLIN)

        while not self.stop_event.isSet():
            # We only start polling on both sockets if at least
            # one server has already been seen
            if self._servers:
                poller = self._poller_proxy
            else:
                poller = self._poller_backend

            socks = dict(poller.poll(self.polling_interval * 1000))
            if socks.get(frontend) == zmq.POLLIN:
                frames = frontend.recv_multipart()
                frames_size = len(frames)
                if frames_size == SERVICE_QUERY_SIZE:
                    self._handle_service_query(frontend, frames)
                elif frames_size == CLIENT_REQUEST_SIZE:
                    self._handle_client_request(backend, frames)

            if socks.get(backend) == zmq.POLLIN:
                frames = backend.recv_multipart()
                frames_size = len(frames)

                assert frames_size in [REPLY_SIZE, CONTROL_REPLY_SIZE]
                if frames_size == REPLY_SIZE:
                    self._handle_server_reply(frontend, frames)
                elif frames_size == CONTROL_REPLY_SIZE:
                    self._handle_server_control(frames)

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

        log.debug("Got server ready signal from: %s" % server_identity)
        if server_identity not in self._servers:
            self._servers.append(server_identity)

    def _handle_client_request(self, backend, request):
        # FIXME if server is not known, we need to answer something
        # need to implement the RFC to make this work
        client_identity, _, payload, server_identity = request
        backend.send_multipart(
            [server_identity, b'', client_identity, b'', payload])

    def _handle_service_query(self, frontend, query):
        client_identity, _, service_identity = query
        reply = b'+' if service_identity in self._servers else b'-'
        frontend.send_multipart([client_identity, b'', reply])
