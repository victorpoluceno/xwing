import pickle
import uuid
import asyncio

from xwing.mailbox.inbound import Inbound
from xwing.mailbox.outbound import Outbound


def resolve(name_or_pid):
    if isinstance(name_or_pid, str):
        if '@' in name_or_pid:
            name, hub_address = name_or_pid.split('@')
            return hub_address, name
        else:
            return '127.0.0.1', name_or_pid

    return name_or_pid


class Mailbox(object):

    def __init__(self, hub_frontend, hub_backend, loop, name):
        self.hub_backend = hub_backend
        self.hub_frontend = hub_frontend
        self.loop = loop
        self.identity = name if name else str(uuid.uuid1())
        self.inbound = Inbound(self.loop, self.hub_backend, self.identity)
        self.outbound = Outbound(self.loop, self.identity)

    def start(self):
        self.loop.create_task(self.inbound.start())

    def stop(self):
        self.inbound.stop()

    @property
    def pid(self):
        return self.hub_frontend, self.identity

    async def recv(self, timeout=None):
        payload = await self.inbound.recv(timeout=timeout)
        return pickle.loads(payload)

    async def send(self, name_or_pid, *args):
        payload = pickle.dumps(args)
        pid = resolve(name_or_pid)
        await self.outbound.send(pid, payload)


class Node(object):

    def __init__(self, loop=None, hub_frontend='127.0.0.1',
                 hub_backend='/var/tmp/xwing.socket'):
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self.hub_frontend = hub_frontend
        self.hub_backend = hub_backend
        self.mailbox_list = []
        self.tasks = []

    def spawn(self, fn, *args, name=None):
        # Create a mailbox for my upper_actor and schedule it to run
        mailbox = Mailbox(self.hub_frontend, self.hub_backend,
                          self.loop, name)
        mailbox.start()

        self.tasks.append(self.loop.create_task(fn(mailbox, *args)))
        self.mailbox_list.append(mailbox)
        return mailbox.pid

    def run(self):
        done, pending = self.loop.run_until_complete(asyncio.wait(
            self.tasks, return_when=asyncio.FIRST_EXCEPTION))

        # If a exception happened on any of waited tasks
        # this forces the exception to buble up
        for future in done:
            future.result()

    def stop(self):
        '''Loop stop.'''
        for task in asyncio.Task.all_tasks():
            task.cancel()

        self.loop.run_forever()
        self.loop.close()


node = Node()
spawn, run, stop = node.spawn, node.run, node.stop
