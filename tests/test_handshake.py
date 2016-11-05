import asyncio

import pytest

from xwing.exceptions import HandshakeTimeoutError, HandshakeProtocolError
from xwing.network.handshake import (
    connect_handshake, accept_handshake, HANDSHAKE_ACK_SIGNAL)
from xwing.network.transport.stream import get_stream_connection
from xwing.concurrency import TaskPool
from xwing.network.connection import get_connection
from tests.helpers import run_until_complete, syntetic_buffer


class TestHandshake:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        self.stream_connection = get_stream_connection('dummy')(
            self.loop, None)
        self.task_pool = TaskPool(self.loop)
        self.connection = get_connection('real')(self.loop,
                                                 self.stream_connection,
                                                 self.task_pool)

    @run_until_complete
    async def test_connect_handshake(self):
        syntetic_buffer.put(HANDSHAKE_ACK_SIGNAL + b'\n')
        assert await connect_handshake(self.connection, 'foo')

    @run_until_complete
    async def test_connect_handshake_protocol_error(self):
        syntetic_buffer.put(b'garbage\n')
        with pytest.raises(HandshakeProtocolError):
            await connect_handshake(self.connection, 'foo')

    @run_until_complete
    async def test_connect_handshake_timeout_error(self):
        syntetic_buffer.put(0.2)
        with pytest.raises(HandshakeTimeoutError):
            await connect_handshake(self.connection, 'foo', 0.1)

    @run_until_complete
    async def test_accept_handshake(self):
        syntetic_buffer.put(HANDSHAKE_ACK_SIGNAL + b';bar\n')
        assert await accept_handshake(self.connection, 'foo')

    @run_until_complete
    async def test_accept_handshake_protocol_error(self):
        syntetic_buffer.put(b'garbage\n')
        with pytest.raises(HandshakeProtocolError):
            await accept_handshake(self.connection, 'foo')

    @run_until_complete
    async def test_accept_handshake_timeout_error(self):
        syntetic_buffer.put(0.2)
        with pytest.raises(HandshakeTimeoutError):
            await accept_handshake(self.connection, 'foo', 0.1)
