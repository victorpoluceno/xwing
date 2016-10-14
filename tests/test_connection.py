import asyncio

import pytest

from xwing.exceptions import HeartbeatFailureError
from xwing.mailbox import TaskPool
from xwing.network.connection import Connection
from xwing.network.transport.stream import get_stream_connection
from tests.helpers import run_until_complete


class TestConnection:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        self.stream_connection = get_stream_connection('dummy')(
            self.loop, None)
        self.task_pool = TaskPool(self.loop)
        self.connection = Connection(self.loop, self.stream_connection,
                                     self.task_pool)

    def test_send(self):
        assert self.connection.send(b'foo') == b'foo'

    @run_until_complete
    async def test_recv(self):
        self.stream_connection.lines = [b'foo\n']
        assert await self.connection.recv() == b'foo'

    @run_until_complete
    async def test_liveness_zero_raises_error(self):
        self.connection.liveness = 1
        with pytest.raises(HeartbeatFailureError):
            await self.connection.run_heartbeat_loop(heartbeat_interval=0.1)
