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

    async def readline(self):
        return await self.reader.readline()

    def write(self, data):
        return self.writer.write(data)

    async def drain(self):
        return await self.writer.drain()
