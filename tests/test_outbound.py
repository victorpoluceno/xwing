import asyncio
from unittest import mock

import pytest

from xwing.mailbox.outbound import (Outbound, MaxRetriesExceededError,
                                    DEFAULT_FRONTEND_PORT)
from tests.helpers import make_coro_mock


class TestOutbound:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        self.outbound = Outbound(self.loop, 'myid')

    def test_send(self):
        conn = make_coro_mock()
        conn.send = make_coro_mock()
        self.outbound.connect = make_coro_mock()
        self.outbound.connect.coro.return_value = conn
        assert self.loop.run_until_complete(self.outbound.send('foo', b'bar'))
        assert conn.send.called

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
