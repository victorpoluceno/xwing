from gevent import monkey
monkey.patch_all()

import sys
sys.path.append('.')

import logging
logging.basicConfig(level=logging.DEBUG)

from xwing import Client, Proxy, Server


class TestClient:

    def setup_class(self):
        proxy = Proxy('tcp://*:5555', 'ipc:///tmp/0')
        proxy.run()

        self.server = Server('ipc:///tmp/0')
        self.server.run()

        self.client = Client('tcp://localhost:5555')

    def test_auto_identity(self):
        assert self.client.identity

    def test_send_and_recv(self):
        assert self.client.send(self.server.identity, 'ping')
        assert self.server.recv() == 'ping'

    def test_send_to_fail(self):
        client = Client('tcp://localhost:5555', retry_timeout=0.01)
        assert not client.send('unkown', 'hi')
