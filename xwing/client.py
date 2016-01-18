import zmq


REQUEST_RETRIES = 3
REQUEST_TIMEOUT = 2500


class Client:

    def __init__(self, endpoint, identity):
        self.endpoint = endpoint
        self.identity = identity

        self._context = zmq.Context()
        self._poller = zmq.Poller()

        self._socket = self._setup()

    def send(self, server, payload):
        payload = bytes(payload, 'utf-8') + server
        retries_left = REQUEST_RETRIES
        self._socket.send_multipart([payload, server])

        expect_reply = True
        while expect_reply:
            socks = dict(self._poller.poll(REQUEST_TIMEOUT))
            if socks.get(self._socket) == zmq.POLLIN:
                reply = self._socket.recv()
                if not reply:
                    break

                if reply == payload:
                    retries_left = REQUEST_RETRIES
                    expect_reply = False
                else:
                    print("E: Malformed reply from server: %s" % reply)
            else:
                print("W: No response from server, retryin...")

                # Socket is confused. Close and remove it.
                self._socket.setsockopt(zmq.LINGER, 0)
                self._socket.close()
                self._poller.unregister(self._socket)
                retries_left -= 1
                if retries_left == 0:
                    print("E: Server seems to be offline, abandoning")
                    break

                print("I: Reconnecting and resending")
                # Create new connection
                self._socket = self._setup()
                self._socket.send_multipart([payload, server])

    def _setup(self):
        print("I: Connecting to server...")
        socket = self._context.socket(zmq.REQ)
        socket.setsockopt_string(zmq.IDENTITY, self.identity)

        self._poller.register(socket, zmq.POLLIN)
        print(self.endpoint)
        socket.connect(self.endpoint)
        return socket
