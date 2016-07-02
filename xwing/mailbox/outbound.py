import asyncio

from xwing.socket.client import Client


class Outbound(object):

    def __init__(self, loop, identity):
        # FIXME need to fix this fixed hub address
        self.client = Client(loop, '127.0.0.1:5555', identity)
        self.connections = {}  # TODO add pool with max size
        self.stop_event = asyncio.Event()

    def stop(self):
        self.stop_event.set()

    async def connect(self, identity):
        if identity in self.connections:
            return

        while not self.stop_event.is_set():
            try:
                conn = await self.client.connect(identity)
            except ConnectionError:
                print('Retrying connection..')
                await asyncio.sleep(0.1)
                continue
            else:
                break

        print('Connected!')
        self.connections[identity] = conn

    async def send(self, identity, data):
        await self.connect(identity)
        conn = self.connections[identity]
        await conn.send(data)
