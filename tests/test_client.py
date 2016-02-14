from gevent import monkey
monkey.patch_all()

import sys
sys.path.append('.')

from xwing import Client, Proxy, Server


def setup_module():
    proxy = Proxy('tcp://*:5555', 'ipc:///tmp/0')
    proxy.run()


class TestClient:

    def setup_class(self):
        self.server = Server('ipc:///tmp/0')
        self.server.run()

        self.client = Client('tcp://localhost:5555')

    def test_auto_identity(self):
        assert self.client.identity

    def test_recv(self):
        assert self.client.send(
            'tcp://localhost:5555', self.server.identity, 'ping')
        assert self.server.recv() == 'ping'
