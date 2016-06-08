import json
import uuid
import asyncio

from xwing.socket.server import Server
from xwing.socket.client import Client


mailbox_map = {}  # keep track of all process mailbox


class Mailbox:

    def __init__(self, hub_frontend, node_id, loop):
        self.loop = loop
        self.hub_frontend = hub_frontend
        self.node_id = node_id
        self.identity = str(uuid.uuid1())
        self.actor_id = '{0}@{1}'.format(self.node_id, self.identity)
        self.queue = asyncio.Queue()

        mailbox_map[self.actor_id] = self  # self register at mailbox map

    async def recv(self):
        return await self.queue.get()

    async def send(self, actor_id, message):
        # create a client connecton for this actor
        client = Client(self.loop, self.hub_frontend, self.actor_id)

        # connect to the node id where destination actor lives
        node_id, _ = actor_id.split('@')
        
        #import pdb; pdb.set_trace()

        while True:
            try:
                conn = await client.connect(node_id)
            except ConnectionError as e:
                print(e)
                print('Reconnecting...')
                await asyncio.sleep(1)
                continue
            else:
                print('Good, we are connected!')
                break

        # encode a message and send
        await conn.send_str(json.dumps((actor_id, self.actor_id, message)))
        conn.close()


class Node:

    def __init__(self, loop, hub_frontend, hub_backend):
        self.loop = loop
        self.hub_frontend = hub_frontend
        self.hub_backend = hub_backend
        self.identity = str(uuid.uuid1())

    async def run(self):
        #import pdb; pdb.set_trace()
        
        socket_server = Server(self.loop, self.hub_backend, self.identity)
        await socket_server.listen()
        print('Node is accepting connections...')
        conn = await socket_server.accept()

        while True:
            payload = await conn.recv_str()
            if not payload:
                break

            # enqueue message received
            print(payload)
            recipient, sender, message = json.loads(payload)
            mailbox[recipient].put((sender, message))

    def spawn(self, fn, *args):
        # create a mailbox for my upper_actor and schedule it to run
        mailbox = Mailbox(self.hub_frontend, self.identity, self.loop)
        self.loop.create_task(fn(mailbox, *args))
        return mailbox.actor_id
