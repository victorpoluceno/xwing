import asyncio

from xwing.network.controller import Controller
from xwing.network.transport.stream.client import get_stream_client
from xwing.mailbox import TaskPool, Settings
from xwing.network.handshake import HANDSHAKE_ACK_SIGNAL
from tests.helpers import run_until_complete, run_once, syntetic_buffer


class TestController:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        self.settings = Settings()
        self.task_pool = TaskPool(self.loop)
        self.controller = Controller(
            self.loop, self.settings, self.task_pool,
            get_stream_client('dummy'))
        self.controller.stop_event.is_set = run_once(
            self.controller.stop_event.is_set, return_value=True)

    @run_until_complete
    async def test_run_outbound(self):
        syntetic_buffer.put(HANDSHAKE_ACK_SIGNAL + b'\n')
        await self.controller.put_outbound(('127.0.0.1', 'foo'), b'bar')
        await self.controller.run_outbound(timeout=0.1)
