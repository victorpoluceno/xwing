import sys
sys.path.append('.')

import logging
logging.basicConfig(level=logging.DEBUG)

import pytest

from xwing.proxy import Proxy
from xwing.socket.client import SocketClient
from xwing.socket.server import SocketServer


def send(proxy, server, data):
    client = SocketClient(proxy, 'client1')
    return client.send(server, data)


class TestServer:

    @classmethod
    def setup_class(cls):
        cls.proxy = Proxy('tcp://*:5555', 'ipc:///tmp/0')
        cls.proxy.run(forever=False)

        cls.server = SocketServer('ipc:///tmp/0')
        cls.server.bind()

        cls.client = SocketClient('tcp://localhost:5555', 'client1')

    @classmethod
    def teardown_class(cls):
        cls.client.close()
        cls.server.close()
        cls.proxy.stop()

    def test_auto_identity(self):
        assert self.server.identity

    def test_send_and_recv(self):
        data = 'ping'
        self.client.send(self.server.identity, data)
        self.server.send(self.server.recv())
        assert self.client.recv() == data

    def test_send_and_recv_raw(self):
        data = 'ping'
        self.client.send(self.server.identity, data)
        self.server.send_raw(self.server.recv_raw())
        assert self.client.recv() == data

    def test_recv_no_data(self):
        assert self.server.recv(timeout=0.1) is None

    def test_send_without_recv(self):
        with pytest.raises(AssertionError):
            self.server.send('ping')
