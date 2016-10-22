import asyncio

from xwing.mailbox import Settings
from xwing.network.connection import get_connection
from xwing.network.transport.stream import get_stream_connection
from xwing.network.inbound import Inbound
from xwing.mailbox import TaskPool
from tests.helpers import run_once, run_until_complete, syntetic_buffer


class TestInbound:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        settings = Settings()
        self.inbound = Inbound(self.loop, settings)
        self.inbound.stop_event.is_set = run_once(
            self.inbound.stop_event.is_set, return_value=True)

        self.stream_connection = get_stream_connection('dummy')(
            self.loop, None)
        self.task_pool = TaskPool(self.loop)
        self.connection = get_connection('real')(
            self.loop, self.stream_connection, self.task_pool)

    @run_until_complete
    async def test_get_with_timeout_error(self):
        assert await self.inbound.get(timeout=0.1) is None

    @run_until_complete
    async def test_get_return_put_value(self):
        await self.inbound.inbox.put('foo')
        assert await self.inbound.get() == 'foo'

    @run_until_complete
    async def test_run_recv_loop(self):
        syntetic_buffer.put(b'foo\n')
        await self.inbound.run_recv_loop(self.connection)
        assert await self.inbound.get() == b'foo'

    @run_until_complete
    async def test_stop_nothing_gets_done(self):
        self.inbound.stop()
        await self.inbound.run_recv_loop(self.connection)
        assert await self.inbound.get(0.1) is None

    @run_until_complete
    async def test_run_recv_loop_may_raise_timeout_error(self):
        syntetic_buffer.put(0.2)
        await self.inbound.run_recv_loop(self.connection, timeout=0.1)
