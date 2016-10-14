import asyncio

async def connection_to_stream(connection, loop):
    return await asyncio.open_connection(sock=connection.sock,
                                         loop=loop)


class StreamConnection:

    def __init__(self, loop, connection):
        self.loop = loop
        self.connection = connection

    async def initialize(self):
        self.reader, self.writer = await connection_to_stream(
            self.connection, self.loop)
        return True

    async def readline(self):
        return await self.reader.readline()

    def write(self, data):
        return self.writer.write(data)

    async def drain(self):
        return await self.writer.drain()


class DummyStreamConnection:

    def __init__(self, loop, connection):
        self.loop = loop
        self.connection = connection
        self.lines = []
        self.sleep = None

    async def initialize(self):
        return True

    async def readline(self):
        if self.sleep:
            await asyncio.sleep(self.sleep)
            return None

        return self.lines.pop()

    def write(self, data):
        return True

    async def drain(self):
        return True


kind_map = {
    'real': StreamConnection,
    'dummy': DummyStreamConnection,
}


def get_stream_connection(kind):
    return kind_map[kind]
