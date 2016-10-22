from xwing.network.transport.socket.server import Server
from xwing.network.transport.stream import (
    StreamConnection, DummyStreamConnection)


class StreamServer(Server):

    async def accept(self):
        stream_connection = StreamConnection(self.loop, await super(
            StreamServer, self).accept())
        await stream_connection.initialize()
        return stream_connection


class DummyStreamServer:

    def __init__(self, loop, settings):
        self.loop = loop
        self.settings = settings

    async def listen(self):
        return True

    async def accept(self):
        stream_connection = DummyStreamConnection(self.loop, None)
        await stream_connection.initialize()
        return stream_connection


kind_map = {
    'real': StreamServer,
    'dummy': DummyStreamServer,
}


def get_stream_server(kind):
    return kind_map[kind]
