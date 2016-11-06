import asyncio

import pytest

from xwing.exceptions import HeartbeatFailureError, ConnectionAlreadyExists
from xwing.concurrency.taskset import TaskSet
from xwing.network.connection import Connection, Repository, HEARTBEAT_SIGNAL
from xwing.network.transport.stream import get_stream_connection
from tests.helpers import run_until_complete, syntetic_buffer


class TestRepository:

    def setup_method(self, method):
        self.repository = Repository()

    def test_add_get(self):
        self.repository.add(1, 'foo')
        assert self.repository.get('foo') == 1

    def test_add_existing_connection_fails(self):
        self.repository.add(1, 'foo')
        with pytest.raises(ConnectionAlreadyExists):
            self.repository.add(1, 'foo')

    def test_contains(self):
        self.repository.add(1, 'foo')
        assert 'foo' in self.repository
        assert 'bar' not in self.repository

    def test_identity_must_be_string(self):
        with pytest.raises(TypeError):
            b'foo' in self.repository


class TestConnection:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        self.stream_connection = get_stream_connection('dummy')(
            self.loop, None)
        self.taskset = TaskSet(self.loop)
        self.connection = Connection(self.loop, self.stream_connection,
                                     self.taskset)

    def test_send(self):
        assert self.connection.send(b'foo') == b'foo'

    @run_until_complete
    async def test_recv(self):
        syntetic_buffer.put(b'foo\n')
        assert await self.connection.recv() == b'foo'

    @run_until_complete
    async def test_recv_data_and_heartbeat(self):
        syntetic_buffer.put(b'foo\n')
        syntetic_buffer.put(HEARTBEAT_SIGNAL + b'\n')
        assert await self.connection.recv() == b'foo'

    @run_until_complete
    async def test_recv_partial_data(self):
        syntetic_buffer.put(b'foo')
        assert await self.connection.recv() is None

    @run_until_complete
    async def test_liveness_zero_raises_error(self):
        self.connection.liveness = 1
        with pytest.raises(HeartbeatFailureError):
            await self.connection.run_heartbeat_loop(heartbeat_interval=0.1)
