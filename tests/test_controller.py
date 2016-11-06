import asyncio

from xwing.network.controller import Controller
from xwing.network.transport.stream.client import get_stream_client
from xwing.network.transport.stream.server import get_stream_server
from xwing.concurrency.taskset import TaskSet
from xwing.node import Settings
from xwing.network.handshake import HANDSHAKE_ACK_SIGNAL
from tests.helpers import run_until_complete, run_once, syntetic_buffer


class TestController:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        self.settings = Settings()
        self.taskset = TaskSet(self.loop)
        self.controller = Controller(
            self.loop, self.settings, self.taskset,
            get_stream_client('dummy'),
            get_stream_server('dummy'))
        self.controller.stop_event.is_set = run_once(
            self.controller.stop_event.is_set, return_value=True)

    @run_until_complete
    async def test_run_outbound(self):
        syntetic_buffer.put(HANDSHAKE_ACK_SIGNAL + b'\n')
        await self.controller.put_outbound(('127.0.0.1', 'foo'), b'bar')
        await self.controller.run_outbound(timeout=0.1)

    @run_until_complete
    async def test_run_outbound_with_not_data(self):
        await self.controller.run_outbound(timeout=0.1)

    @run_until_complete
    async def test_run_inbound(self):
        syntetic_buffer.put(b'data\n')
        syntetic_buffer.put(HANDSHAKE_ACK_SIGNAL + b';bar\n')
        await self.controller.run_inbound()
        assert await self.controller.get_inbound() == b'data'

    @run_until_complete
    async def test_run_and_stop(self):
        self.controller.start()
        self.controller.stop()
