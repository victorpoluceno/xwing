import pickle
import uuid
import asyncio

from xwing.mailbox.inbound import Inbound
from xwing.mailbox.outbound import Outbound


class Mailbox:

    def __init__(self, hub_backend, hub_frontend, loop):
        self.loop = loop
        self.hub_frontend = hub_frontend
        self.hub_backend = hub_backend
        self.identity = str(uuid.uuid1())
        self.inbound = Inbound(self.loop, self.hub_backend, self.identity)
        self.outbound = Outbound(self.loop, self.hub_frontend, self.identity)

    def start(self):
        self.loop.create_task(self.inbound.start())

    def stop(self):
        self.inbound.stop()
        self.outbound.stop()

    async def recv(self):
        payload = await self.inbound.recv()
        sender, message = pickle.loads(payload)
        return sender, message

    async def send(self, identity, message):
        payload = pickle.dumps((self.identity, message))
        await self.outbound.send(identity, payload)


class Node:

    def __init__(self, loop, hub_frontend, hub_backend):
        self.loop = loop
        self.hub_frontend = hub_frontend
        self.hub_backend = hub_backend
        self.mailbox_list = []
        self.tasks = []

    def spawn(self, fn, *args):
        # Create a mailbox for my upper_actor and schedule it to run
        mailbox = Mailbox(self.hub_backend, self.hub_frontend, self.loop)
        mailbox.start()

        self.tasks.append(self.loop.create_task(fn(mailbox, *args)))
        self.mailbox_list.append(mailbox)
        return mailbox.identity

    def run(self):
        try:
            done, pending = self.loop.run_until_complete(asyncio.wait(
                self.tasks, return_when=asyncio.FIRST_EXCEPTION))

            # If a exception happened on any of waited tasks
            # this forces the exception to buble up
            for future in done:
                future.result()
        except KeyboardInterrupt:
            self.stop()

    def run_until_complete(self):
        self.run()
        self.stop()

    def stop(self):
        '''Loop stop.'''
        for mailbox in self.mailbox_list:
            mailbox.stop()

        pending = asyncio.Task.all_tasks()
        self.loop.run_until_complete(asyncio.wait(pending))
        self.loop.close()
