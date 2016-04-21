import sys
sys.path.append('.')

import logging
logging.basicConfig(level=logging.DEBUG)

import pytest

from xwing.proxy import Proxy
from xwing.socket.client import SocketClient
from xwing.socket.server import SocketServer


class TestClient:

    @classmethod
    def setup_class(cls):
        cls.proxy = Proxy('tcp://*:5555', 'ipc:///tmp/0')
        cls.proxy.run(forever=False)

        cls.server = SocketServer('ipc:///tmp/0')
        cls.server.bind()

        cls.client = SocketClient('tcp://localhost:5555')

    @classmethod
    def teardown_class(cls):
        cls.client.close()
        cls.server.close()
        cls.proxy.stop()

    def test_auto_identity(self):
        assert self.client.identity

    def test_send_and_recv(self):
        assert self.client.send(self.server.identity, 'ping')
        assert self.server.recv() == 'ping'

    def test_recv_no_data(self):
        assert self.client.recv(timeout=0.1) is None

    @pytest.mark.skip(reason="need to implement RFC")
    def test_send_to_fail(self):
        client = SocketClient('tcp://localhost:5555')
        assert not client.send('unkown', 'hi')
