import sys
sys.path.append('.')

import time
import threading
import logging
logging.basicConfig(level=logging.DEBUG)

import pytest

from xwing.proxy import Proxy
from xwing.socket.client import Client
from xwing.socket.server import Server


FRONTEND_ADDRESS = '127.0.0.1:5555'
BACKEND_ADDRESS = '/var/tmp/xwing.socket'


def start_echo_server(stop_event):
    server = Server(BACKEND_ADDRESS, 'server0')
    server.listen()

    conn = server.accept()
    while not stop_event.isSet():
        conn.send(conn.recv())


def setup_module(module):
    module.proxy = proxy = Proxy(FRONTEND_ADDRESS, BACKEND_ADDRESS)
    proxy.run(forever=False)
    time.sleep(0.5)

    module.stop_event = stop_event = threading.Event()
    module.thread = threading.Thread(target=start_echo_server,
                                     args=(stop_event,), daemon=False)
    module.thread.start()


def teardown_module(module):
    module.stop_event.set()
    module.thread.join()
    module.proxy.stop()


class TestIntegration:

    @classmethod
    def setup_class(cls):
        cls.client = Client(FRONTEND_ADDRESS)
        cls.client_conn = cls.client.connect('server0')

    @classmethod
    def teardown_class(cls):
        cls.client_conn.close()

    def test_auto_identity(self):
        assert self.client.identity

    def test_send_and_recv_str(self):
        data = 'ping'
        self.client_conn.send_str(data)
        assert self.client_conn.recv_str() == data

    def test_send_and_recv(self):
        data = b'ping'
        self.client_conn.send(data)
        assert self.client_conn.recv() == data

    @pytest.mark.skip(reason="need to implement timeout support")
    def test_recv_no_data(self):
        assert self.server_conn.recv(timeout=0.1) is None
