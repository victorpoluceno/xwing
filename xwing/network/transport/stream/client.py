from xwing.network.transport.socket.client import Client
from xwing.network.transport.stream import StreamConnection, DummyStreamConnection


class StreamClient(Client):

    async def connect(self, service):
        stream_connection = StreamConnection(self.loop, await super(
            StreamClient, self).connect(service))
        await stream_connection.initialize()
        return stream_connection


class DummyStreamClient:

    def __init__(self, loop, remote_hub_frontend, identity):
        self.loop = loop
        self.remote_hub_frontend = remote_hub_frontend
        self.identity = identity

    async def connect(self, service):
        stream_connection = DummyStreamConnection(self.loop, None)
        await stream_connection.initialize()
        return stream_connection

kind_map = {
    'real': StreamClient,
    'dummy': DummyStreamClient,
}


def get_stream_client(kind):
    return kind_map[kind]
