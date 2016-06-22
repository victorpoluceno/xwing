import json
import uuid
import asyncio

from xwing.socket.server import Server
from xwing.socket.client import Client


class Mailbox:

    def __init__(self, hub_backend, hub_frontend, loop):
        self.loop = loop
        self.hub_frontend = hub_frontend
        self.hub_backend = hub_backend
        self.identity = str(uuid.uuid1())

    def start(self):
        self.server = Server(self.loop, self.hub_backend, self.identity)
        self.loop.run_until_complete(self.server.listen())
        print('%s is listening.' % self.identity)

    async def recv(self):
        conn = await self.server.accept()
        payload = await conn.recv_str()
        sender, message = json.loads(payload)
        conn.close()
        return sender, message

    async def send(self, identity, message):
        # Create a client connecton for this actor
        client = Client(self.loop, self.hub_frontend, self.identity)
        while True:
            try:
                print('Connecting to %s' % identity)
                conn = await client.connect(identity)
            except ConnectionError:
                await asyncio.sleep(1)
                continue
            else:
                break

        await conn.send_str(json.dumps((self.identity, message)))
        conn.close()


class Node:

    def __init__(self, loop, hub_frontend, hub_backend):
        self.loop = loop
        self.hub_frontend = hub_frontend
        self.hub_backend = hub_backend

    def spawn(self, fn, *args):
        # Create a mailbox for my upper_actor and schedule it to run
        mailbox = Mailbox(self.hub_backend, self.hub_frontend, self.loop)
        mailbox.start()

        self.loop.create_task(fn(mailbox, *args))
        return mailbox.identity

    def run(self):
        pending = asyncio.Task.all_tasks()
        self.loop.run_until_complete(asyncio.gather(*pending))
