import asyncio

from xwing.socket.server import Server


class Inbound(object):

    def __init__(self, loop, hub_backend, identity):
        self.loop = loop
        self.identity = identity
        self.server = Server(loop, hub_backend, identity)
        self.connections = []  # TODO add pool with max size
        self.inbox = asyncio.Queue(loop=self.loop)
        self.stop_event = asyncio.Event()

    async def start(self):
        await self.server.listen()
        self.loop.create_task(self.accept_loop())
        self.loop.create_task(self.recv_loop())
        print('%s is listening.' % self.identity)

    def stop(self):
        self.stop_event.set()

    async def recv(self):
        return await self.inbox.get()

    async def accept_loop(self):
        while not self.stop_event.is_set():
            await asyncio.sleep(0.001)
            try:
                conn = await asyncio.wait_for(
                    self.server.accept(), 1.0)
            except asyncio.TimeoutError:
                continue

            self.connections.append(conn)

    async def recv_loop(self):
        while not self.stop_event.is_set():
            await asyncio.sleep(0.001)
            for conn in self.connections:
                try:
                    data = await asyncio.wait_for(
                        conn.recv(), 5.0)
                    if not data:
                        continue
                except asyncio.TimeoutError:
                    continue

                await self.inbox.put(data)
