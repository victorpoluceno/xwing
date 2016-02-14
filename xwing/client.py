import uuid
import logging
log = logging.getLogger(__name__)

import zmq.green as zmq


RETRY_NUMBER = 3
RETRY_TIMEOUT = 2500

ZMQ_LINGER = 0


class Client(object):
    '''The Client implementation.

    Provide a Client that knowns how to connect to a Proxy service
    send requests and waiting for replies. The Client implements a retry
    mecanics.

    :param multiplex_endpoint: Mutliplex service address to connect.
    :type multiplex_endpoint: str
    :param identity: Unique client identification. If not set uuid1 will be
    used.
    :type identity: str
    :param retry_number: Number of retries to try if got no answer and timeout.
    :param retry_timeout: Timeout to wait for an answer before retrying.

    Usage::

      >>> from xwing.client import Client
      >>> client = Client('tcp://localhost:5555', 'client1')
      >>> client.send('tcp://localhost:5555', 'server0', 'ping')
    '''

    def __init__(self, multiplex_endpoint, identity=None,
                 retry_number=RETRY_NUMBER, retry_timeout=RETRY_TIMEOUT):
        self.multiplex_endpoint = multiplex_endpoint
        self.identity = str(uuid.uuid1()) if not identity else identity
        self.retry_number = retry_number
        self.retry_timeout = retry_timeout

        self._context = zmq.Context()
        self._poller = zmq.Poller()
        self._socket = self._setup_zmq_socket(
            self._context, self._poller, zmq.REQ, self.identity)

    def send(self, server_multiplex_endpoint, server_identity, request,
             encoding='utf-8'):
        '''
        Send a request to Server on a Multiplex. The send method implements
        a retry by checking if we got positive answer from destination and
        retrying otherwise.

        :param server_multiplex_endpoint: The multiplex endpoint where the
        server lives.
        :param server_identity: The Identity of the destination server.
        :param request: The payload to send to Server.
        :param encoding: The desired encoding to be user on this request.
        '''
        server_identity = bytes(server_identity, encoding)
        request = bytes(request, encoding)
        self._socket_send(server_multiplex_endpoint, server_identity, request)

        got_reply = False
        retries_left = self.retry_number
        while retries_left:
            reply = self._socket_recv(self.retry_timeout)
            # If we reply is equal to the payload we sent
            # it means we delivered to right destination
            if reply == request:
                got_reply = True
                break

            log.error("Malformed reply from server: %s" % reply)
            log.info("Reconnecting and resending...")
            self._disconnect_zmq_socket()
            self._socket = self._setup_zmq_socket(self._context, self._poller,
                                                  zmq.REQ, self.identity)
            self._socket_send(
                server_multiplex_endpoint, server_identity, request)
            retries_left -= 1

        return got_reply

    def _socket_send(self, multiplex_endpoint, server_identity, payload):
        pack = [payload, server_identity]

        # If proxy equal to our multiplex we just send to our own multiplex
        if multiplex_endpoint == self.multiplex_endpoint:
            self._socket.send_multipart(pack)
        else:
            self._socket.send_multipart(pack + [multiplex_endpoint])

    def _socket_recv(self, timeout):
        socks = dict(self._poller.poll(timeout))
        if socks.get(self._socket) != zmq.POLLIN:
            return None

        return self._socket.recv()

    def _disconnect_zmq_socket(self):
        # Socket is confused. Close and remove it.
        self._socket.setsockopt(zmq.LINGER, ZMQ_LINGER)
        self._socket.close()
        self._poller.unregister(self._socket)

    def _setup_zmq_socket(self, context, poller, kind, identity):
        socket = context.socket(kind)
        poller.register(socket, zmq.POLLIN)
        socket.setsockopt_string(zmq.IDENTITY, identity)
        socket.connect(self.multiplex_endpoint)
        return socket
