from gevent import monkey
monkey.patch_all()

import sys
sys.path.append('.')

import pytest

from xwing import Client, Proxy, Server
from xwing.server import NoData


def setup_module():
    proxy = Proxy('tcp://*:5555', 'ipc:///tmp/0')
    proxy.run()


def send(server, data):
    client = Client('tcp://localhost:5555', 'client1')
    client.send(server, data)


class TestServer:

    def setup_class(self):
        self.server = Server('ipc:///tmp/0')
        self.server.run()

    def test_auto_identity(self):
        assert self.server.identity

    def test_recv_no_data(self):
        with pytest.raises(NoData):
            self.server.recv()

    def test_recv(self):
        send(self.server.identity, 'ping')
        assert self.server.recv() == 'ping'
