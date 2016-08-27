import asyncio
from unittest import mock
from concurrent import futures

import pytest

from xwing.mailbox import Inbound


def make_coro_mock():
    coro = mock.Mock(name="CoroutineResult")
    corofunc = mock.Mock(name="CoroutineFunction",
                         side_effect=asyncio.coroutine(coro))
    corofunc.coro = coro
    return corofunc


def run_once(f, return_value=None):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
        return return_value
    wrapper.has_run = False
    return wrapper


class TestInbound:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        self.inbound = Inbound(self.loop, '/var/tmp/xwing.socket', 'myid')
        self.inbound.stop_event.is_set = run_once(
            self.inbound.stop_event.is_set, return_value=True)
        self.conn = make_coro_mock()
        self.conn.recv = make_coro_mock()

    def test_start_call_listen_accept_loop(self):
        self.inbound.server.listen = make_coro_mock()
        self.inbound.run_accept_loop = make_coro_mock()
        self.loop.run_until_complete(self.inbound.start())
        assert self.inbound.run_accept_loop.called
        assert self.inbound.server.listen.called

    def test_stop(self):
        self.inbound.stop()
        self.inbound.server.accept = make_coro_mock()
        self.loop.run_until_complete(self.inbound.run_accept_loop())
        assert not self.inbound.server.accept.called

        self.loop.run_until_complete(
            self.inbound.run_recv_loop(self.conn, 1.0))
        assert not self.conn.recv.called

    def test_recv(self):
        self.inbound.inbox.get = make_coro_mock()
        self.inbound.inbox.get.coro.return_value = 'foo'
        assert self.loop.run_until_complete(self.inbound.recv(0.1)) == 'foo'

    def test_recv_raises_timeout(self):
        with pytest.raises(futures.TimeoutError):
            assert not self.loop.run_until_complete(self.inbound.recv(0.1))

    def test_run_accept_loop(self):
        self.inbound.accept_one = make_coro_mock()
        self.inbound.accept_one.coro.return_value = self.conn
        self.inbound.run_recv_loop = make_coro_mock()
        self.loop.run_until_complete(self.inbound.run_accept_loop())
        assert self.inbound.run_recv_loop.called

    def test_run_accept_loop_no_connection(self):
        self.inbound.accept_one = make_coro_mock()
        self.inbound.accept_one.coro.return_value = None
        self.inbound.run_recv_loop = make_coro_mock()
        self.loop.run_until_complete(self.inbound.run_accept_loop())
        assert not self.inbound.run_recv_loop.called

    def test_accept_one(self):
        self.inbound.server.accept = make_coro_mock()
        self.inbound.server.accept.coro.return_value = self.conn
        conn = self.loop.run_until_complete(self.inbound.accept_one(1))
        assert conn == self.conn

    def test_accept_one_catch_timeout_error(self):
        self.inbound.server.accept = make_coro_mock()
        self.inbound.server.accept.side_effect = asyncio.TimeoutError
        conn = self.loop.run_until_complete(self.inbound.accept_one(1))
        assert conn is None

    def test_run_recv_loop(self):
        self.inbound.recv_one = make_coro_mock()
        self.inbound.recv_one.coro.return_value = 'foo'
        self.inbound.inbox.put = make_coro_mock()
        self.loop.run_until_complete(self.inbound.run_recv_loop(
                                     self.conn, 1.0))
        assert self.inbound.inbox.put.called

    def test_run_recv_loop_with_no_data(self):
        self.inbound.recv_one = make_coro_mock()
        self.inbound.recv_one.coro.return_value = ''
        self.inbound.inbox.put = make_coro_mock()
        self.loop.run_until_complete(self.inbound.run_recv_loop(
                                     self.conn, 1.0))
        assert not self.inbound.inbox.put.called

    def test_recv_one(self):
        self.conn.recv.coro.return_value = 'foo'
        data = self.loop.run_until_complete(self.inbound.recv_one(
                                            self.conn, 1.0))
        assert data == 'foo'

    def test_recv_one_catch_timeout_error(self):
        self.conn.recv.coro.side_effect = asyncio.TimeoutError
        data = self.loop.run_until_complete(self.inbound.recv_one(
                                            self.conn, 1.0))
        assert data is None
