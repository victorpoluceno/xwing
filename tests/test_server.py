import gevent
from gevent import monkey
monkey.patch_all()

import sys
sys.path.append('.')

import pytest

import logging
logging.basicConfig(level=logging.DEBUG)

from xwing import Client, Proxy, Server
from xwing.server import NoData


def send(proxy, server, data):
    client = Client(proxy, 'client1')
    return client.send(server, data)


class TestServer:

    def setup_class(self):
        self.server = Server('ipc:///tmp/0')
        self.server.run()

        self.proxy = Proxy('tcp://*:5555', 'ipc:///tmp/0')
        self.proxy.run()

    def test_auto_identity(self):
        assert self.server.identity

    def test_recv_no_data(self):
        with pytest.raises(NoData):
            self.server.recv()

    def test_recv(self):
        send('tcp://localhost:5555', self.server.identity, 'ping')
        assert self.server.recv() == 'ping'


class TestServerReconnect:

    def setup_class(self):
        self.proxy = Proxy('tcp://*:6666', 'ipc:///tmp/1',
                           heartbeat_interval=0.1)
        self.proxy.run()

        self.server = Server('ipc:///tmp/1', heartbeat_interval=0.1,
                             reconnect_interval=0.1)
        self.server.run()

    def test_reconnect(self):
        self.proxy.stop()

        # Forces a missing heartbeat so server try to reconnect
        # and then start the proxy again
        gevent.sleep(0.2)
        self.proxy.run()

        assert send('tcp://localhost:6666', self.server.identity, 'ping')
