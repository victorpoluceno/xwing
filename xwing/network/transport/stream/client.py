from xwing.network.transport.socket.client import Client
from xwing.network.transport.stream import StreamConnection


class StreamClient(Client):

    async def connect(self, service):
        stream_connection = StreamConnection(self.loop, await super(
            StreamClient, self).connect(service))
        await stream_connection.initialize()
        return stream_connection
