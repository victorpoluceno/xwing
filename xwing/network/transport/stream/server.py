import asyncio

from xwing.network.transport.socket.server import Server
from xwing.network.transport.stream import StreamConnection


class StreamServer(Server):

    async def accept(self):
        try:
            stream_connection = StreamConnection(self.loop, await super(
                StreamServer, self).accept())
            await stream_connection.initialize()
        except asyncio.TimeoutError:
            return None

        return stream_connection


class DummyStreamServer:

    def __init__(self, *args, **kwargs):
        pass

    async def listen(self):
        return True

    async def accept(self):
        return True


kind_map = {
    'real': StreamServer,
    'dummy': DummyStreamServer,
}


def get_stream_server(kind):
    return kind_map[kind]
