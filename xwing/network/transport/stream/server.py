from xwing.network.transport.socket.server import Server
from xwing.network.transport.stream import StreamConnection


class StreamServer(Server):

    async def accept(self):
        stream_connection = StreamConnection(self.loop, await super(
            StreamServer, self).accept())
        await stream_connection.initialize()
        return stream_connection
