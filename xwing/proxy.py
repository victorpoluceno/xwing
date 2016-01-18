import time

import zmq

PPP_READY = b"\x01"  # Signals worker is ready
PPP_HEARTBEAT = b"\x02"  # Signals worker heartbeat

HEARTBEAT_INTERVAL = 1.0   # Seconds


class Proxy:

    def __init__(self, frontend_endpoint, backend_endpoint):
        self.frontend_endpoint = frontend_endpoint
        self.backend_endpoint = backend_endpoint

    def start(self):
        context = zmq.Context()

        frontend = context.socket(zmq.ROUTER)
        frontend.bind(self.frontend_endpoint)

        backend = context.socket(zmq.ROUTER)
        backend.bind(self.backend_endpoint)

        poll_backend = zmq.Poller()
        poll_backend.register(backend, zmq.POLLIN)

        poll_proxy = zmq.Poller()
        poll_proxy.register(frontend, zmq.POLLIN)
        poll_proxy.register(backend, zmq.POLLIN)

        servers = []
        heartbeat_at = time.time() + HEARTBEAT_INTERVAL

        while True:
            if not servers:
                poller = poll_backend
            else:
                poller = poll_proxy

            socks = dict(poller.poll(HEARTBEAT_INTERVAL * 1000))
            if socks.get(frontend) == zmq.POLLIN:
                # Get client request, route to server
                message = frontend.recv_multipart()
                request = [message.pop(-1), b''] + message
                backend.send_multipart(request)

            if socks.get(backend) == zmq.POLLIN:
                message = backend.recv_multipart()
                if message[-1] == PPP_READY:
                    if not message[0] in servers:
                        servers.append(message[0])
                else:
                    frontend.send_multipart(message[2:])

            # Send heartbeats to idle workers if it's time
            if time.time() >= heartbeat_at:
                for server in servers:
                    msg = [server, PPP_HEARTBEAT]
                    backend.send_multipart(msg)

                heartbeat_at = time.time() + HEARTBEAT_INTERVAL
