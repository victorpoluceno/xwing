import asyncio

import pytest

from xwing.exceptions import MaxRetriesExceededError
from xwing.mailbox import Settings
from xwing.network.outbound import Outbound, Connector
from xwing.network.transport.stream.client import get_stream_client
from tests.helpers import run_until_complete, make_coro_mock


class TestConnector:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        self.settings = Settings()
        client_factory = get_stream_client('dummy')
        self.connector = Connector(self.loop, self.settings,
                                   client_factory)
        self.stream = client_factory(self.loop, 'localhost:5555', 'foo')

    def test_create_client(self):
        stream = self.connector.create_client('localhost')
        assert stream.remote_hub_frontend == 'localhost:5555'
        assert stream.identity == self.settings.identity

    @run_until_complete
    async def test_connect_client(self):
        await self.connector.connect_client(self.stream, 'bar')

    @run_until_complete
    async def test_connect_client_raise_error(self):
        self.stream.connect = make_coro_mock()
        self.stream.connect.side_effect = ConnectionError
        with pytest.raises(MaxRetriesExceededError):
            await self.connector.connect_client(
                self.stream, 'bar', max_retries=1)

    @run_until_complete
    async def test_connect_return_connection(self):
        assert await self.connector.connect(('localhost', 'foo'))


class TestOutbound:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        settings = Settings()
        self.outbound = Outbound(self.loop, settings)

    @run_until_complete
    async def test_get_with_timeout_error(self):
        assert await self.outbound.get(timeout=0.1) is None

    @run_until_complete
    async def test_get_after_put(self):
        await self.outbound.put(*('foo', 'bar')) is None
        assert await self.outbound.get() == ('foo', 'bar')
