import asyncio
from unittest import mock

import pytest

from xwing.mailbox.outbound import (Outbound, MaxRetriesExceededError,
                                    DEFAULT_FRONTEND_PORT)
from tests.helpers import make_coro_mock, run_once


class TestOutbound:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        self.outbound = Outbound(self.loop, 'myid')
        self.outbound.stop_event.is_set = run_once(
            self.outbound.stop_event.is_set, return_value=True)

    def test_start_call_listen_accept_loop(self):
        self.outbound.run_send_loop = make_coro_mock()
        self.outbound.start()
        assert self.outbound.run_send_loop.called

    def test_stop(self):
        self.outbound.stop()
        outbox = make_coro_mock()
        outbox.put = make_coro_mock()
        self.outbound.outbox = outbox
        self.loop.run_until_complete(self.outbound.run_send_loop())
        assert not self.outbound.outbox.called

    def test_send(self):
        outbox = make_coro_mock()
        outbox.put = make_coro_mock()
        self.outbound.outbox = outbox
        assert self.loop.run_until_complete(self.outbound.send('foo', b'bar'))
        outbox.put.assert_called_with(('foo', b'bar'))

    def test_run_send_loop(self):
        outbox = make_coro_mock()
        outbox.get = make_coro_mock()
        outbox.get.coro.return_value = ('foo', b'bar')
        self.outbound.outbox = outbox

        class Conn:
            pass

        conn = Conn()
        conn.send = make_coro_mock()
        self.outbound.connect = make_coro_mock()
        self.outbound.connect.coro.return_value = conn

        self.loop.run_until_complete(self.outbound.run_send_loop())
        assert self.outbound.connect.called
        assert conn.send.called

    def test_run_send_loop_with_no_data(self):
        outbox = make_coro_mock()
        outbox.get = make_coro_mock()
        outbox.get.coro.side_effect = asyncio.TimeoutError
        self.outbound.outbox = outbox
        self.outbound.connect = make_coro_mock()
        self.loop.run_until_complete(self.outbound.run_send_loop())
        assert not self.outbound.connect.called

    def test_connect(self):
        pid = '127.0.0.1', 'foo'
        self.outbound.create_client = mock.Mock()
        self.outbound.connect_client = make_coro_mock()
        self.outbound.connect_client.coro.return_value = 'conn'
        assert self.loop.run_until_complete(
            self.outbound.connect(pid)) == 'conn'
        assert pid[0] in self.outbound.clients
        assert pid[1] in self.outbound.connections

    def test_connect_client(self):
        class Client:
            pass

        client = Client()
        client.connect = make_coro_mock()
        client.connect.coro.return_value = 'conn'
        assert self.loop.run_until_complete(
            self.outbound.connect_client(client, 'foo', 1, 0.1)) == 'conn'

    def test_connect_client_with_connection_error(self):
        class Client:
            pass

        client = Client()
        client.connect = make_coro_mock()
        client.connect.coro.side_effect = ConnectionError
        with pytest.raises(MaxRetriesExceededError):
            self.loop.run_until_complete(
                self.outbound.connect_client(client, 'foo', 1, 0.1)) == 'conn'

    @mock.patch('xwing.mailbox.outbound.Client')
    def test_create_client(self, client_klass):
        assert self.outbound.create_client('127.0.0.1')
        client_klass.assert_called_with(
            self.outbound.loop, '127.0.0.1:{0}'.format(DEFAULT_FRONTEND_PORT),
            'myid')
