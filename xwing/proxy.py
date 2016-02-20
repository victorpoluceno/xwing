import logging
import time

import gevent

import zmq.green as zmq


SIGNAL_READY = b"\x01"  # Signals server is ready
SIGNAL_HEARTBEAT = b"\x02"  # Signals server heartbeat

HEARTBEAT_INTERVAL = 1.0

REPLY_SIZE = 5
CONTROL_REPLY_SIZE = 2

ZMQ_LINGER = 0

log = logging.getLogger(__name__)


class Proxy:
    '''The Proxy implementation.

    Provides a Proxy that known how to route messages
    between clients and servers.

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

        self._run_loop = False
        self._servers = []
        self._init_zmq_context()

    def run(self):
        '''Run the server loop'''
        self._run_loop = True
        self._greenlet_loop = gevent.spawn(self._run_zmq_poller)
        gevent.sleep(0)  # forces the greenlet to be scheduled

    def join(self):
        '''Join the server loop, this will block until loop ends'''
        self._greenlet_loop.join()

    def stop(self):
        '''Loop stop.'''
        self._run_loop = False
        self._greenlet_loop.kill()
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

        heartbeat_at = time.time() + self.heartbeat_interval

        while self._run_loop:
            # We only start polling on both sockets if at least
            # one server has already benn seen
            if self._servers:
                poller = self._poller_proxy
            else:
                poller = self._poller_backend

            socks = dict(poller.poll(self.heartbeat_interval * 1000))
            if socks.get(frontend) == zmq.POLLIN:
                frames = frontend.recv_multipart()
                self._handle_client_request(backend, frames)

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
        log.debug('Sending reply from server to client')
        frontend.send_multipart([client_identity, _, payload])

    def _handle_server_control(self, control):
        # Handle control messages from server to proxy.
        # Message format: [server_identity, payload]
        server_identity, payload = control
        assert payload == SIGNAL_READY

        log.info("Got server ready signal from: %s" % server_identity)
        if server_identity not in self._servers:
            self._servers.append(server_identity)

    def _handle_client_request(self, backend, request):
        client_identity, _, payload, server_identity = request
        backend.send_multipart(
            [server_identity, b'', client_identity, b'', payload])
